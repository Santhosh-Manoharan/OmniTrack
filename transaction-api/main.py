"""
OmniTrack Transaction API
FastAPI service for PostgreSQL transaction CRUD operations.
n8n calls this via HTTP Request nodes.
"""
import os
import json
import re
from decimal import Decimal
from datetime import date, datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
PG_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "omnitrack"),
    "user": os.getenv("POSTGRES_USER", "omnitrack"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}


def get_conn():
    return psycopg2.connect(**PG_CONFIG)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="OmniTrack Transaction API", version="1.0")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TransactionCreate(BaseModel):
    transaction_date: Optional[str] = None
    amount: float
    currency: str = "INR"
    transaction_type: str  # DEBIT / CREDIT / TRANSFER
    merchant_name: Optional[str] = None
    merchant_upi: Optional[str] = None
    bank_name: Optional[str] = None
    account_identifier: Optional[str] = None
    category: Optional[str] = None
    source: str = "bank_email"
    source_ref: Optional[str] = None
    raw_text: Optional[str] = None
    document_id: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        # Allow extras so n8n can pass whatever LLM returns
        extra = "allow"


class TransactionResponse(BaseModel):
    id: str
    transaction_date: Optional[date] = None
    amount: Decimal
    currency: str
    transaction_type: str
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    source: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Category auto-classification
# ---------------------------------------------------------------------------
def classify_category(merchant_name: Optional[str], raw_text: Optional[str] = None) -> str:
    """Auto-classify based on keywords in merchant name or raw text."""
    text = f"{merchant_name or ''} {raw_text or ''}".lower()
    keywords = {
        "groceries": ["reliance", "bigbazaar", "dmart", "kirana", "supermarket", "blaze", "more", "grocery", "big bazaar"],
        "utilities": ["electricity", "water", "gas", "broadband", "jio", "airtli", "vodafone", "bsnl", "idea", "bill", "dth", "recharge"],
        "transport": ["uber", "ola", "rapido", "petrol", "diesel", "metro", "bus", "auto", "zoom", "drive", "fuel", "parking"],
        "food": ["swiggy", "zomato", "restaurant", "cafe", "pizza", "burger", "dunkin", "mcdonald", "kfc", "food", "bakery", "coffee", "starbucks"],
        "entertainment": ["netflix", "spotify", "prime", "hotstar", "movie", "inox", "pvr", "game", "play", "disney", "sony", "music"],
        "medical": ["hospital", "pharmacy", "doctor", "apollo", "medplus", "lab", "health", "clinic", "dr.", "medical", "medicine", "diagnostic"],
        "education": ["school", "college", "course", "udemy", "coursera", "fee", "tuition", "coaching", "book", "exam"],
        "rent": ["rent", "maintenance", "housing", "society", "landlord", "lease"],
        "shopping": ["amazon", "flipkart", "myntra", "store", "mall", "purchase", "shop", "online", "meesho", "ajio"],
        "salary": ["salary", "income", "credited", "payment received", "freelance", "bonus", "dividend"],
        "transfer": ["upi", "transfer", "sent to", "received from", "neft", "rtgs", "imps", "self transfer"],
        "fuel": ["petrol", "diesel", "fuel", "hpcl", "iocl", "bpcl", "shell", "hp pump", "indianoil"],
        "insurance": ["insurance", "lic", "policy", "premium", "max life", "icici pru", "bajaj allianz"],
        "emi": ["emi", "loan", "hdfc loan", "sbi loan", "axis loan", "payment due", "installment"],
    }
    for category, words in keywords.items():
        for word in words:
            if word in text:
                return category
    return "other"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    try:
        conn = get_conn()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.post("/transactions", status_code=201)
async def create_transaction(txn: TransactionCreate):
    """Insert a new transaction."""
    # Auto-classify category if not provided
    if not txn.category:
        txn.category = classify_category(txn.merchant_name, txn.raw_text)

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions
                (transaction_date, amount, currency, transaction_type, merchant_name,
                 merchant_upi, bank_name, account_identifier, category, source,
                 source_ref, raw_text, document_id, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id, transaction_date, amount, currency, transaction_type,
                      merchant_name, category, source, created_at
        """, (
            txn.transaction_date, txn.amount, txn.currency, txn.transaction_type,
            txn.merchant_name, txn.merchant_upi, txn.bank_name, txn.account_identifier,
            txn.category, txn.source, txn.source_ref, txn.raw_text,
            txn.document_id, txn.notes,
        ))
        row = cur.fetchone()
        conn.commit()
        col_names = [d[0] for d in cur.description]
        cur.close()
        conn.close()
        return dict(zip(col_names, row))
    except psycopg2.IntegrityError as e:
        raise HTTPException(status_code=409, detail=f"Duplicate or integrity error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/batch", status_code=201)
async def create_transactions_batch(txns: list[dict]):
    """Insert multiple transactions at once (LLM can return arrays)."""
    results = []
    errors = []

    for i, raw in enumerate(txns):
        # Normalize keys from LLM output
        txn_data = {
            "transaction_date": raw.get("date") or raw.get("transaction_date"),
            "amount": float(raw.get("amount", 0)),
            "currency": raw.get("currency", "INR"),
            "transaction_type": raw.get("transaction_type", "DEBIT"),
            "merchant_name": raw.get("merchant_name"),
            "merchant_upi": raw.get("merchant_upi"),
            "bank_name": raw.get("bank_name"),
            "account_identifier": raw.get("account_last4") or raw.get("account_identifier"),
            "category": raw.get("category"),
            "source": raw.get("source", "bank_email"),
            "source_ref": raw.get("source_ref"),
            "raw_text": raw.get("raw_text"),
        }
        if not txn_data["category"]:
            txn_data["category"] = classify_category(
                txn_data["merchant_name"], str(raw)
            )
        txn = TransactionCreate(**txn_data)
        try:
            result = await create_transaction(txn)
            results.append(result)
        except HTTPException as e:
            errors.append({"index": i, "detail": e.detail})

    return {"inserted": len(results), "errors": len(errors), "results": results, "error_details": errors}


@app.post("/transactions/from-ollama", status_code=201)
async def create_from_llm(raw: dict):
    """
    Accept raw Ollama response, extract JSON array, and insert transactions.
    n8n passes the Ollama HTTP response body here.
    """
    import re

    response_text = raw.get("response", "")
    # Extract JSON array from response
    match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if not match:
        raise HTTPException(status_code=400, detail=f"No JSON array found in response: {response_text[:200]}")

    try:
        txns = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON parse error: {e}")

    if not isinstance(txns, list):
        txns = [txns]

    results = await _insert_txns(txns, response_text)
    return {"inserted": len(results["results"]), "errors": len(results["errors"]), "results": results["results"], "error_details": results["errors"]}


@app.post("/transactions/from-email", status_code=201)
async def create_from_email(data: dict):
    """
    Accept email text, call Ollama to parse, extract JSON, and insert transactions.
    n8n just sends the email text — no need to deal with Ollama JSON formatting.
    Expected: { "email_text": "...", "email_from": "...", "email_subject": "...", "email_date": "..." }
    """
    import re
    import httpx

    email_text = data.get("email_text", "")
    email_from = data.get("email_from", "")
    email_subject = data.get("email_subject", "")
    email_date = data.get("email_date", "")

    prompt = f"""Parse this Indian bank transaction email and return ONLY a JSON array. Even if there is only one transaction, wrap it in an array [].

Email Date: {email_date}
Email Subject: {email_subject}
Email From: {email_from}

Email Content:
{email_text}

Return ONLY JSON array in this exact format:
[{{"amount": number, "currency": "INR", "transaction_type": "DEBIT or CREDIT or TRANSFER", "merchant_name": "clean brand name or null", "merchant_upi": "UPI ID or null", "bank_name": "bank name", "account_last4": "last 4 digits or null", "category": "groceries/utilities/transport/food/entertainment/medical/education/rent/shopping/salary/transfer/fuel/insurance/emi/other", "date": "YYYY-MM-DD", "time": "HH:MM or null"}}]

Rules:
- amount: number only (no Rs/INR/commas)
- merchant_upi: clean UPI ID (swiggyupi@axisbank)
- merchant_name: brand name only (Swiggy, Amazon, etc.)
- If field not found, use null
- Return ONLY the JSON array, no explanation, no markdown"""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post("http://ollama:11434/api/generate", json={
                "model": "mistral:7b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 500}
            })
        response_text = resp.json().get("response", "")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    # Extract JSON array
    match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if not match:
        raise HTTPException(status_code=400, detail=f"No JSON array found: {response_text[:300]}")

    try:
        txns = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON parse error: {e}, raw: {match.group()[:200]}")

    if not isinstance(txns, list):
        txns = [txns]

    results = await _insert_txns(txns, email_text, source="bank_email")
    return {"inserted": len(results["results"]), "errors": len(results["errors"]), "results": results["results"], "error_details": results["errors"]}


async def _insert_txns(txns: list, raw_text: str, source: str = "bank_email"):
    """Helper to insert a list of transaction dicts."""
    results = []
    errors = []
    for i, item in enumerate(txns):
        raw_amount = item.get("amount")
        if raw_amount is None:
            errors.append({"index": i, "detail": "amount is null, skipping"})
            continue
        try:
            amount = float(raw_amount)
        except (TypeError, ValueError) as e:
            errors.append({"index": i, "detail": f"Invalid amount '{raw_amount}': {e}"})
            continue
        txn_data = {
            "transaction_date": item.get("date") or item.get("transaction_date"),
            "amount": amount,
            "currency": item.get("currency", "INR") or "INR",
            "transaction_type": item.get("transaction_type", "DEBIT") or "DEBIT",
            "merchant_name": item.get("merchant_name"),
            "merchant_upi": item.get("merchant_upi"),
            "bank_name": item.get("bank_name"),
            "account_identifier": item.get("account_last4") or item.get("account_identifier"),
            "category": item.get("category"),
            "source": item.get("source", source),
            "raw_text": raw_text[:1000],
        }
        if not txn_data["category"]:
            txn_data["category"] = classify_category(txn_data["merchant_name"], str(item))
        try:
            txn = TransactionCreate(**txn_data)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO transactions
                    (transaction_date, amount, currency, transaction_type, merchant_name,
                     merchant_upi, bank_name, account_identifier, category, source,
                     source_ref, raw_text)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id, transaction_date, amount, currency, transaction_type,
                          merchant_name, category, source, created_at
            """, (
                txn.transaction_date, txn.amount, txn.currency, txn.transaction_type,
                txn.merchant_name, txn.merchant_upi, txn.bank_name, txn.account_identifier,
                txn.category, txn.source, txn.source_ref, txn.raw_text,
            ))
            row = cur.fetchone()
            conn.commit()
            col_names = [d[0] for d in cur.description]
            cur.close()
            conn.close()
            results.append(dict(zip(col_names, row)))
        except Exception as e:
            errors.append({"index": i, "detail": str(e)})
    return {"results": results, "errors": errors}


@app.get("/transactions")
async def list_transactions(limit: int = 50, offset: int = 0, category: Optional[str] = None):
    """List transactions with optional filtering."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if category:
        cur.execute(
            "SELECT * FROM transactions WHERE category=%s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (category, limit, offset),
        )
    else:
        cur.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/transactions/{txn_id}")
async def get_transaction(txn_id: str):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM transactions WHERE id=%s", (txn_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@app.get("/summary/monthly")
async def monthly_summary():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM monthly_summary")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/summary/daily")
async def daily_spending():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM daily_spending LIMIT 30")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/summary/merchants")
async def merchant_spending():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM merchant_spending LIMIT 50")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/categories")
async def list_categories():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# SMS Capture
# ---------------------------------------------------------------------------
@app.post("/sms/capture")
async def sms_capture(data: dict):
    """
    Receive SMS text via webhook and auto-categorize.
    Expected: { "from": "AD-SBI", "text": "...", "timestamp": "..." }
    """
    text = data.get("text", "")
    sender = data.get("from", "")

    # Classify the SMS
    category = classify_category(None, text)

    # Try to extract amount with regex
    import re
    amount_match = re.search(r'(?:Rs\.?|₹|INR)\s*([0-9,]+\.?[0-9]*)', text)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0

    # Determine type
    txn_type = "DEBIT" if any(w in text.lower() for w in ["debited", "spent", "paid", "withdrawn"]) else \
               "CREDIT" if any(w in text.lower() for w in ["credited", "received", "deposited"]) else "DEBIT"

    merchant = classify_category(None, text)  # rough

    return {
        "success": True,
        "amount": amount,
        "type": txn_type,
        "category": category,
        "sender": sender,
        "raw_text": text[:500],
    }
