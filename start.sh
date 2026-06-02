#!/bin/bash
# OmniTrack Startup Script

set -e
cd "$(dirname "$0")"

# Check .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Edit .env with your passwords, then run this script again."
    echo "   Required: POSTGRES_PASSWORD, N8N_PASSWORD, FIREFLY_APP_KEY"
    exit 1
fi

echo "🚀 Starting OmniTrack Financial Suite..."
echo ""

# Start all services
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check services
echo ""
echo "✅ Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps

echo ""
echo "🌐 Access Your Services:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Firefly III (Transactions):  http://localhost:8080"
echo "  n8n (Workflows):             http://localhost:5678"
echo "  Paperless-ngx (Documents):   http://localhost:8000"
echo "  Budibase (Dashboard):        http://localhost:10000"
echo "  Grafana (Monitoring):        http://localhost:3000"
echo "  Prometheus (Metrics):        http://localhost:9090"
echo "  Ollama (Local AI):           http://localhost:11434"
echo ""
echo "  Nginx (Unified gateway):     http://localhost:80"
echo ""

# Pull Ollama model if not present
echo "🤖 Checking Ollama model..."
if command -v curl &>/dev/null; then
    MODEL=${OLLAMA_MODEL:-mistral:7b}
    if ! curl -s http://localhost:11434/api/tags | grep -q "$MODEL"; then
        echo "   Pulling $MODEL (first time only, ~4GB download)..."
        curl -s http://localhost:11434/api/pull -d "{\"name\":\"$MODEL\"}" &
        echo "   This runs in background. Check progress with: curl http://localhost:11434/api/tags"
    else
        echo "   ✅ $MODEL already available"
    fi
fi

echo ""
echo "🎉 OmniTrack is ready!"
