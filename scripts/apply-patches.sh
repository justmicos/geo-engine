#!/usr/bin/env bash
# =============================================================================
# Apply GEOFlow patches — called by setup.sh after cloning kengine-src.
# Copies patched/added files from patches/ into kengine-src/.
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

PATCHES_DIR="$(cd "$(dirname "$0")/../patches" && pwd)"
TARGET_DIR="$(cd "$(dirname "$0")/../kengine-src" && pwd)"

if [ ! -d "$TARGET_DIR" ]; then
    warn "kengine-src not found at $TARGET_DIR. Run setup.sh first."
    exit 1
fi

info "Applying patches to kengine-src..."

# Copy each patched file, preserving directory structure
cd "$PATCHES_DIR"

find . -type f -name "*.php" -o -name "*.json" | while read -r file; do
    src="$PATCHES_DIR/$file"
    dst="$TARGET_DIR/$file"
    dst_dir=$(dirname "$dst")

    mkdir -p "$dst_dir"
    cp "$src" "$dst"
    info "  Patched: $file"
done

# Run migrations if not already run
if [ -f "$TARGET_DIR/artisan" ]; then
    info "Checking for new migrations..."
    cd "$TARGET_DIR"
    php artisan migrate --force 2>/dev/null && info "Migrations applied" || warn "Migration skipped or failed"
fi

info "Patches applied successfully."
