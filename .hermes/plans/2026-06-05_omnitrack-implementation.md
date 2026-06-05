# OmniTrack Implementation Plan

> **Date:** 2026-06-05
> **Status:** Phase 3 in progress — bank email tracking pipeline

## Goal

Build a working personal expense tracking system that:
1. **Automatically captures transactions** from bank notification emails (Gmail trigger)
2. **Extracts structured data** (amount, merchant, category, date) using local LLM (Ollama/Mistral)
3. **Stores transactions** in PostgreSQL for querying and reporting
4. **Archives emails** in Paperless-ngx for document management
5. **Supports receipt photo upload** via webhook for cash transactions

## Current Context

### What's Done
- ✅ 8 Docker containers running (PostgreSQL, Redis, n8n, Paperless, Ollama, Upload Helper, Prometheus, Grafana)
- ✅ Database schema v2 (`database/schema-v2.sql`) — transactions, categories, merchants, views
- ✅ 4 n8n workflow files created
- ✅ Security: Paperless API token regenerated after exposure
- ✅ Knowledge graph: 12 Obsidian notes documenting everything

### What's NOT Done
- ❌ n8n workflows have NOT been tested end-to-end
- ❌ Ollama credential not configured in n8n
- ❌ Gmail OAuth2 not configured
- ❌ Database schema not run in PostgreSQL
- ❌ No actual transaction data flowing yet

### Known Issues
- **Structured Output Parser** was too strict for mistral:7b output → removed, switched to HTTP Request approach
- **n8n Code node** broken in v2.22.6 → use HTTP Request nodes instead
- **Ollama credential URL** must be `http://ollama:11434` (Docker hostname), not `localhost`

## Proposed Approach

### Step 1: Test Bank Email Parsing (Immediate Next Step)

**File:** `n8n-workflows/02-Bank-Email-Test-v3.json`

This is the simplest test workflow — manual trigger + sample SBI email + HTTP Request to Ollama.

**Actions:**
1. Open n8n at http://localhost:5678
2. Import `02-Bank-Email-Test-v3.json`
3. Add Ollama API credential: Settings → Credentials → Ollama API → Base URL: `http://ollama:11434`
4. Select the Ollama credential in the workflow node
5. Run the workflow
6. Verify output: should return parsed JSON with amount=500, merchant=Swiggy, category=food, etc.

**If it fails:**
- Check Ollama logs: `docker logs ot-ollama`
- Try `02-Bank-Email-Test-v2.json` (uses chainLlm instead of HTTP Request)
- Simplify the prompt further

### Step 2: Setup Database

**File:** `database/schema-v2.sql`

**Actions:**
1. Connect to PostgreSQL: `docker exec -it ot-postgres psql -U omnitrack -d omnitrack`
2. Run the schema SQL
3. Verify tables: `\dt`
4. Insert test data manually to verify

### Step 3: Setup Gmail OAuth2

**Actions:**
1. Go to https://console.cloud.google.com
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop application)
4. Add redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`
5. Download credentials JSON
6. In n8n: Settings → Credentials → Add → Gmail OAuth2
7. Paste Client ID + Client Secret
8. Click "Connect my account" → authorize

### Step 4: Production Bank Email Workflow

**File:** `n8n-workflows/01-Bank-Email-Tracker-v2.json`

**Actions:**
1. Import the workflow
2. Configure Gmail credential
3. Configure Ollama credential
4. Test with real bank email
5. Activate the workflow

### Step 5: Receipt Upload Workflow

**File:** `n8n-workflows/03-Receipt-Upload.json`

**Actions:**
1. Import the workflow
2. Configure Ollama credential
3. Test by sending POST request to webhook URL with image
4. Verify document appears in Paperless

### Step 6: SMS Capture (Future)

For transactions <₹500 that only get SMS:
1. Setup Google Messages for Web or Android Tasker
2. Forward SMS to n8n webhook
3. Parse with same LLM approach

### Step 7: Dashboard & Reports (Future)

1. Run Metabase or connect to PostgreSQL
2. Build spending dashboards
3. Monthly reports
4. Budget alerts

## Files Likely to Change

| File | Change |
|------|--------|
| `n8n-workflows/01-Bank-Email-Tracker-v2.json` | May need prompt tuning, error handling |
| `n8n-workflows/02-Bank-Email-Test-v3.json` | May need simplification if parsing fails |
| `database/schema-v2.sql` | May need additional fields after testing |
| `docker-compose.yml` | May add Metabase service later |
| `.env` | May add new environment variables |

## Tests / Validation

1. **Unit test:** Import test workflow → run → verify JSON output
2. **Integration test:** Send real bank email → verify transaction in PostgreSQL
3. **End-to-end test:** Gmail trigger → Ollama parse → Paperless storage → verify document
4. **Receipt test:** Upload image → verify extracted data + Paperless document

## Risks, Tradeoffs, and Open Questions

### Risks
1. **Ollama parsing reliability** — mistral:7b may not always return valid JSON. Mitigation: use HTTP Request approach with manual JSON extraction (indexOf/lastIndexOf)
2. **Gmail API rate limits** — may hit limits with frequent polling. Mitigation: use webhooks instead of polling
3. **Bank email format changes** — banks may change email format. Mitigation: flexible prompt + fallback parsing

### Tradeoffs
1. **Google Sheets vs PostgreSQL** — Sheets is simpler for viewing, PostgreSQL is better for querying. Decision: use PostgreSQL as primary, optionally sync to Sheets later
2. **chainLlm vs HTTP Request** — chainLlm is cleaner but Structured Output Parser was too strict. Decision: use HTTP Request with careful prompt engineering
3. **Paid APIs vs Local LLM** — Gemini/Groq are more reliable but cost money. Decision: stick with Ollama (free) even if prompt engineering is harder

### Open Questions
1. Should we use Google Sheets as a secondary output for easy viewing?
2. How to handle banks that send PDF statements instead of HTML emails?
3. Should we add a manual review step before saving transactions?
4. How to handle duplicate transactions (email forwarded to multiple addresses)?

## Recommended Immediate Action

**Start with Step 1** — import `02-Bank-Email-Test-v3.json` in n8n and test. This is the smallest possible test that validates the core pipeline:
- Ollama can parse bank emails → structured JSON

If this works, everything else is just wiring. If it doesn't, we need to debug the prompt or try a different approach.
