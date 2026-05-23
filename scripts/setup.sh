#!/usr/bin/env bash
set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
command -v docker &>/dev/null || { error "Docker required"; exit 1; }
if [ ! -d "geoflow-src" ]; then
    info "Cloning GEOFlow..."
    git clone --depth=1 https://github.com/yaojingang/GEOFlow.git geoflow-src
fi
[ ! -f ".env" ] && cp .env.example .env && warn "Edit .env to set AI_API_KEY"
info "Building Docker images..."
docker compose build
info "Starting services..."
docker compose up -d
info "GEOEngine running at http://localhost:${APP_PORT:-18080}/geo_admin"
