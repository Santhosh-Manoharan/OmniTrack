# n8n Workflow Import — Step by Step

## You're logged in at http://localhost:5678 ✅

## Step 1: Add Environment Variables

1. Click your **profile icon** (bottom left) → **Settings**
2. Go to **Environment Variables** (or **Variables**)
3. Add these:

| Name | Value |
|------|-------|
| `PAPERLESS_API_TOKEN` | `e61f76876d0bb609a95eba80bf3c81a75e702e15` |
| `SLACK_WEBHOOK_URL` | *(leave blank for now, add later)* |

## Step 2: Import Workflows

1. Click **Workflows** (left sidebar)
2. Click **Import from File** (top right)
3. Navigate to `C:\Users\Santhosh\OmniTrack\n8n-workflows\`
4. Import in this order:

### 2a. Import `01-receipt-test.json`
- This is a test workflow with Manual Trigger
- After importing, click **Execute Workflow**
- Check the last node — should show extracted JSON
- ✅ If this works, Ollama + Paperless connection is good

### 2b. Import `02-receipt-production.json`
- This is the production Gmail workflow
- Before activating, you need to add Gmail OAuth2 credential
- Skip activation for now

### 2c. Import `03-document-expiry.json`
- Daily 6 AM document expiry alerts
- Can activate immediately — uses Paperless API only

### 2d. Import `04-monthly-reconciliation.json`
- Monthly 28th reconciliation report
- Can activate immediately

## Step 3: Test the Receipt Pipeline

1. Open workflow **"Receipt Test"**
2. Click **Execute Workflow**
3. Watch each node execute (green checkmark = success)
4. Last node should show extracted JSON:

```json
{
  "vendor": "Reliance Fresh",
  "date": "2025-06-01",
  "amount": 787.5,
  "currency": "INR",
  "category": "groceries",
  "tax": 37.5,
  "description": "Rice, Oil, Vegetables",
  "context": "personal"
}
```

5. Check Paperless at http://localhost:8000 — document should appear

## Step 4: Setup Gmail (Optional — for production workflow)

1. Go to https://console.cloud.google.com
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 credentials** (Desktop application)
4. Add authorized redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`
5. Download credentials
6. In n8n: **Credentials** → **Add Credential** → **Gmail OAuth2**
7. Paste Client ID + Client Secret
8. Click **Connect my account** → authorize with your Gmail
9. Now activate the production workflow

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama node shows error | Check: `curl http://localhost:11434/api/tags` |
| Paperless node shows 401 | Verify PAPERLESS_API_TOKEN in n8n env vars |
| Workflow won't activate | Check all credentials are connected |
| "PAPERLESS_API_TOKEN not found" | Add it in Settings → Environment Variables |
