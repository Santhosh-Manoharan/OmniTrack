# OmniTrack Financial Suite

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Building-green.svg)]()
[![Cost](https://img.shields.io/badge/Cost-%240%2Fmonth-brightgreen.svg)]()

Self-hosted financial automation suite — **100% free**, runs on your own hardware. Automate receipt processing, document management, and financial workflows using AI — no cloud, no subscriptions, no vendor lock-in.

## What It Does

- **Receipt Processing** — Email a receipt → AI extracts data → Stored in document vault
- **Document Vault** — OCR-powered document management with tagging and search
- **AI Extraction** — Local LLM (Mistral) extracts vendor, amount, date, category from receipts
- **Workflow Automation** — n8n-powered workflows for alerts, reconciliation, and reports
- **Monitoring** — Prometheus + Grafana dashboards for system health

## Architecture

```
Gmail → n8n → Ollama (AI) → Paperless-ngx (Documents)
                  ↓
              PostgreSQL (Data)
                  ↓
         Prometheus + Grafana (Monitoring)
```

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- 8GB+ RAM recommended
- 10GB+ free disk space

### 1. Clone and Start

```bash
git clone https://github.com/Santhosh-Manoharan/OmniTrack.git
cd OmniTrack
cp .env.example .env
docker compose up -d
```

### 2. Access Services

| Service | URL | Login |
|---------|-----|-------|
| n8n (Workflows) | http://localhost:5678 | Create on first visit |
| Paperless (Documents) | http://localhost:8000 | admin / admin |
| Grafana (Monitoring) | http://localhost:3000 | admin / admin |
| Ollama (AI) | http://localhost:11434 | No auth |

### 3. Import Workflows

1. Open http://localhost:5678 → Create your account
2. Go to **Workflows** → **Import from File**
3. Import files from `n8n-workflows/` folder
4. Run `01-receipt-test.json` to test the AI extraction pipeline

### 4. Test the Pipeline

1. Run the "Receipt to Paperless" workflow in n8n
2. Check http://localhost:8000 — the processed receipt should appear

## Project Structure

```
OmniTrack/
├── docker-compose.yml          # All services configuration
├── .env.example                # Environment variable template
├── .env                        # Your local config (gitignored)
├── start.sh                    # One-command startup
├── stop.sh                     # Graceful shutdown
├── README.md                   # This file
├── LICENSE                     # MIT License
├── CONTRIBUTING.md             # How to contribute
├── SETUP.md                    # Detailed setup guide
├── N8N-IMPORT-GUIDE.md         # n8n workflow import instructions
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── monitoring/
│   └── prometheus.yml          # Prometheus configuration
├── nginx/
│   └── nginx.conf              # Reverse proxy configuration
└── n8n-workflows/
    ├── 01-receipt-test.json           # Test workflow
    ├── 02-receipt-production.json     # Production Gmail workflow
    ├── 03-document-expiry.json        # Document expiry alerts
    └── 04-monthly-reconciliation.json  # Monthly reconciliation
```

## Tech Stack (All Free & Open Source)

| Component | Technology | Cost |
|-----------|-----------|------|
| Workflow Engine | n8n | Free |
| AI/LLM | Ollama + Mistral | Free |
| Document Vault | Paperless-ngx | Free |
| Database | PostgreSQL | Free |
| Cache | Redis | Free |
| Monitoring | Prometheus + Grafana | Free |
| Reverse Proxy | Nginx | Free |
| **Total** | | **$0/month** |

## Roadmap

- [x] Phase 1: Foundation — Docker services running
- [x] Phase 2: AI Extraction — Ollama + receipt parsing
- [x] Phase 3: Document Storage — Paperless-ngx integration
- [ ] Phase 4: Gmail Integration — OAuth2 email trigger
- [ ] Phase 5: Slack Notifications — Workflow alerts
- [ ] Phase 6: Dashboard — Budibase/Metabase financial dashboard
- [ ] Phase 7: Bank Feeds — CSV import automation
- [ ] Phase 8: Multi-User — Keycloak SSO

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Santhosh Manoharan** — [GitHub](https://github.com/Santhosh-Manoharan)
