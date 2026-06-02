# RESUME.md

> Read this when resuming OmniTrack development after a break.

## Where We Left Off

**Phase 1-3 COMPLETE:**
- 7 Docker containers running (PostgreSQL, Redis, n8n, Paperless, Ollama, Prometheus, Grafana)
- AI pipeline verified: receipt text → Ollama extraction → Paperless document
- 4 n8n workflow JSONs created
- GitHub repo: https://github.com/Santhosh-Manoharan/OmniTrack

## Immediate Next Steps

1. **Start services:** `cd OmniTrack && docker compose up -d`
2. **Open n8n:** http://localhost:5678 (create account)
3. **Import workflow:** `n8n-workflows/01-receipt-test.json`
4. **Run it** — should extract receipt data and upload to Paperless
5. **Check Paperless:** http://localhost:8000 — document should appear

## Critical Issues to Remember

- **n8n v2.22.6 Code node is broken** — use HTTP Request nodes instead
- **Ollama model name:** `mistral:7b` (not `mistral`)
- **Paperless tags:** must be integer IDs, not strings
- **Paperless post_document:** needs multipart/form-data (use upload-helper service)
- **Docker Hub EOF in India:** pull images one at a time with retries
- **.env overrides docker-compose.yml** always check both

## Pending Features (Phase 4-6)

- Gmail OAuth2 integration for email trigger
- Slack webhook notifications
- Firefly III transaction hub (image blocked)
- Budibase dashboard (image blocked)

## Knowledge Graph

Full documentation in Obsidian vault: `C:\Users\Santhosh\Documents\Obsidian/`
- Start with: `OT - Knowledge Graph.md` (master index)
- Quick ref: `OT - Quick Reference.md`
- Build status: `OT - Build Status.md`
