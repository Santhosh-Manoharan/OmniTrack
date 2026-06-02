import requests, json, re, os

TOKEN = "e61f76876d0bb609a95eba80bf3c81a75e702e15"
PAPERLESS_URL = "http://localhost:8000/api/documents/post_document/"
HEADERS = {"Authorization": "Token " + TOKEN}

# Extract with Ollama
ollama_resp = requests.post("http://localhost:11434/api/generate", json={
    "model": "mistral:7b",
    "prompt": "Extract data from this receipt. Return ONLY a valid JSON object with keys: vendor, date, amount, currency, category, tax, description, context.\n\nReceipt: RECEIPT. Vendor: Reliance Fresh. Date: 2025-06-01. Total 787.50. Category: groceries. Tax 37.50.",
    "stream": False,
    "options": {"temperature": 0.1}
}, timeout=120)

ai_text = ollama_resp.json().get("response", "")
m = re.search(r'\{[\s\S]*\}', ai_text)
if m:
    data = json.loads(m.group())
    vendor = data.get("vendor", "Unknown")
    date = data.get("date", "2025-01-01")
    print("Extracted: vendor=" + vendor + ", date=" + date)
else:
    print("No JSON found")
    exit(1)

# Create receipt file
receipt_content = "RECEIPT\nVendor: " + vendor + "\nDate: " + date + "\nTotal: 787.50\nTax: 37.50"
temp_path = r"C:\Users\Santhosh\OmniTrack\test_receipt.txt"
with open(temp_path, "w") as f:
    f.write(receipt_content)

# Upload to Paperless
with open(temp_path, "rb") as f:
    files = {"document": ("receipt.txt", f, "text/plain")}
    data = {"title": "Receipt - " + vendor + " - " + date}
    resp = requests.post(PAPERLESS_URL, headers=HEADERS, files=files, data=data, timeout=30)

result = resp.json()
if "id" in result:
    print("SUCCESS! Document ID: " + str(result["id"]))
    print("View: http://localhost:8000/documents/" + str(result["id"]))
else:
    print("Response: " + json.dumps(result)[:300])

os.remove(temp_path)
