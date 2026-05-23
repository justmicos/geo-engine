#!/usr/bin/env bash
set -euo pipefail
OUTPUT_DIR="${1:-./backups}"; mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S); BACKUP_FILE="$OUTPUT_DIR/geoengine_$TIMESTAMP.sql"
echo "💾 Backing up..."
docker compose exec -T postgres pg_dump -U geo_user -d geo_flow --clean --if-exists > "$BACKUP_FILE"
gzip "$BACKUP_FILE"
echo "✅ Saved: ${BACKUP_FILE}.gz"
