#!/usr/bin/env bash
# =============================================================================
# GEOEngine v2.1 — Setup Script (Linux/macOS)
# - Clones GEOFlow source
# - Applies multi-provider patches
# - Detects local LLM engines (Ollama, LM Studio)
# - Creates .env if missing
# - Builds and starts Docker services
# =============================================================================
set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
header() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

command -v docker &>/dev/null || { error "Docker required"; exit 1; }

header "GEOEngine v2.1 Setup"

# 1. Clone GEOFlow source
if [ ! -d "kengine-src" ]; then
    info "Cloning GEOFlow source..."
    git clone --depth=1 https://github.com/justmicos/GEOFlow.git kengine-src
fi

# 2. Apply multi-provider & evolution patches
if [ -f "scripts/apply-patches.sh" ]; then
    header "Applying GEOFlow patches"
    bash scripts/apply-patches.sh
fi

# 3. Auto-detect local LLM engines
header "Local LLM Detection"
if command -v ollama &>/dev/null; then
    OLLAMA_MODEL=$(ollama list 2>/dev/null | head -2 | tail -1 | awk '{print $1}' || echo "")
    if [ -n "$OLLAMA_MODEL" ]; then
        info "Ollama detected: $OLLAMA_MODEL"
    else
        warn "Ollama installed but no models found (run 'ollama pull qwen2.5:7b')"
    fi
else
    warn "Ollama not detected (optional — for local LLM inference)"
fi

if command -v lms &>/dev/null; then
    info "LM Studio CLI detected"
elif [ -f "$HOME/.lmstudio" ] || [ -d "/Applications/LM Studio.app" ]; then
    warn "LM Studio detected but CLI not in PATH"
fi

# 4. Create .env from example if missing
if [ ! -f ".env" ]; then
    header "Creating .env"
    cp .env.example .env
    warn "Edit .env to set at least one AI provider API key:"
    warn "  - OPENAI_API_KEY (OpenAI)"
    warn "  - ANTHROPIC_API_KEY (Claude)"
    warn "  - DEEPSEEK_API_KEY (DeepSeek)"
    warn "  - Or set OLLAMA_BASE_URL for local inference"
    echo ""
    warn "Quick start with DeepSeek:"
    warn "  DEEPSEEK_API_KEY=your_key_here"
    warn "  AI_GATEWAY_ENABLED=true"
else
    info ".env already exists"
fi

# 5. Build and start
header "Starting Services"
info "Building Docker images..."
docker compose build
info "Starting core services..."
docker compose up -d
info "GEOEngine running at http://localhost:${APP_PORT:-18080}/geo_admin"

header "Next Steps"
echo "  1. Open http://localhost:${APP_PORT:-18080}/geo_admin"
echo "  2. Log in and configure AI models in Settings > AI Models"
echo "  3. Or enable AI_GATEWAY_ENABLED=true in .env for auto-routing"
echo ""
echo "  📖 Documentation: https://github.com/justmicos/geo-engine"
