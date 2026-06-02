#!/bin/bash
# OmniTrack Stop Script

cd "$(dirname "$0")"
echo "🛑 Stopping OmniTrack..."
docker compose down
echo "✅ All services stopped. Data preserved in Docker volumes."
echo "   To delete all data: docker compose down -v"
