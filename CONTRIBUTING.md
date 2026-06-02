# Contributing to OmniTrack

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## Development Setup

1. Clone: `git clone https://github.com/Santhosh-Manoharan/OmniTrack.git`
2. Copy env: `cp .env.example .env`
3. Start: `docker compose up -d`
4. Access: http://localhost:5678 (n8n), http://localhost:8000 (Paperless)

## Code Standards

- All workflows should be exported as JSON and placed in `n8n-workflows/`
- Use descriptive workflow names (e.g., `01-receipt-test.json`)
- Document any new environment variables in `.env.example`
- Update `SETUP.md` if adding new services

## Reporting Issues

- Use GitHub Issues
- Include Docker version, OS, and error logs
- Steps to reproduce

## Feature Ideas

- [ ] Gmail OAuth2 credential setup guide
- [ ] Slack webhook integration
- [ ] Bank CSV import workflow
- [ ] Metabase dashboard templates
- [ ] Mobile-responsive dashboard
- [ ] Multi-language receipt support
