# OmniTrack Setup Guide

## Access Services

| Service | URL | Default Login |
|---------|-----|---------------|
| n8n | http://localhost:5678 | admin / (from .env N8N_PASSWORD) |
| Paperless | http://localhost:8000 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Ollama | http://localhost:11434 | No auth |
| Prometheus | http://localhost:9090 | No auth |

## Step 1: Configure Paperless

1. Open http://localhost:8000
2. Login: admin / admin
3. Go to **Settings → API** → Generate token
4. Copy token → add to .env: `PAPERLESS_API_TOKEN=your-token`
5. Create tags: receipt, groceries, utilities, office, meals, travel, medical, entertainment, other

## Step 2: Configure n8n

1. Open http://localhost:5678
2. Login with credentials from .env
3. Go to **Settings → API** → Generate API key
4. Import workflows:
   - Click **Workflows → Import from File**
   - Import each JSON from `n8n-workflows/` folder
5. For Gmail workflow: Add Gmail OAuth2 credential in n8n

## Step 3: Test Ollama AI Extraction

```bash
# Check model is downloaded
curl http://localhost:11434/api/tags

# Test extraction
curl -s http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Extract JSON from this receipt: Vendor: Reliance Fresh, Date: 2025-06-01, Amount: 1250.50, Category: Groceries. Return only JSON with vendor, date, amount, category.",
  "stream": false
}'
```

Expected response: `{"vendor": "Reliance Fresh", "date": "2025-06-01", "amount": 1250.50, "category": "groceries"}`

## Step 4: Configure Slack (Optional)

1. Go to https://api.slack.com/apps → Create New App
2. Enable **Incoming Webhooks**
3. Create webhook for your channel
4. Copy URL → add to .env: `SLACK_WEBHOOK_URL=https://hooks.slack.com/...`

## Step 5: Import Workflows

In n8n (http://localhost:5678):

1. **Workflows → Import from File**
2. Select `n8n-workflows/01-receipt-test.json` → Test first
3. Select `n8n-workflows/02-receipt-production.json` → Production
4. Select `n8n-workflows/03-document-expiry.json` → Alerts
5. Select `n8n-workflows/04-monthly-reconciliation.json` → Reports

## Step 6: Test End-to-End

1. Run `01-receipt-test.json` manually in n8n
2. Check Paperless → Document should appear
3. Check n8n execution log for AI extraction result

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama model not found | `curl http://localhost:11434/api/pull -d '{"name":"mistral"}'` |
| Paperless 502 | Wait 30s for startup, check `docker logs ot-paperless` |
| n8n can't connect to Ollama | Ensure both containers are on same network: `docker network inspect omnitrack_default` |
| Gmail auth fails | Enable Gmail API in Google Cloud Console, create OAuth credentials |

## Stop / Start

```bash
cd C:\Users\Santhosh\OmniTrack
docker compose down    # Stop
docker compose up -d   # Start
docker compose ps      # Check status
```
