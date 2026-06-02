#!/bin/bash
# OmniTrack Image Puller — Auto-retries on failure
# Run this when your connection is available

IMAGES=(
  "postgres:16"
  "redis:7-alpine"
  "nginx:alpine"
  "prom/prometheus:latest"
  "grafana/grafana-oss:latest"
  "n8nio/n8n:latest"
  "ollama/ollama:latest"
  "fireflyiii/core:latest"
  "ghcr.io/paperless-ngx/paperless-ngx:latest"
  "budibase/budibase:latest"
)

MAX_RETRIES=20

echo "============================================"
echo " OmniTrack Image Puller (Auto-Retry)"
echo "============================================"
echo ""

for IMG in "${IMAGES[@]}"; do
  echo "━━━ Pulling: $IMG ━━━"
  
  for i in $(seq 1 $MAX_RETRIES); do
    docker pull "$IMG" 2>&1 && echo "✅ $IMG DONE" && break
    echo "⚠️  Attempt $i failed. Retrying in 10s..."
    sleep 10
  done
  
  echo ""
done

echo ""
echo "============================================"
echo " Pull complete! Checking what we have:"
echo "============================================"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -20
echo ""
echo "Run this to start OmniTrack:"
echo "  cd C:\Users\Santhosh\OmniTrack"
echo "  docker compose up -d"
