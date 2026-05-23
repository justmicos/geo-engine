# GEOEngine v2.1 — Setup Script (Windows PowerShell)
# - Clones GEOFlow source
# - Applies multi-provider patches
# - Detects local LLM engines (Ollama, LM Studio)
# - Creates .env if missing
# - Starts Docker services

$GREEN="Green"; $YELLOW="Yellow"; $CYAN="Cyan"
function Info { Write-Host "[INFO]  " -ForegroundColor $GREEN -NoNewline; Write-Host " $args" }
function Warn { Write-Host "[WARN]  " -ForegroundColor $YELLOW -NoNewline; Write-Host " $args" }
function Header { Write-Host "`n━━━ $args ━━━" -ForegroundColor $CYAN }

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) { Write-Host "[ERROR] Docker required"; exit 1 }

Header "GEOEngine v2.1 Setup"

# 1. Clone GEOFlow source
if (-not (Test-Path "kengine-src")) {
    Info "Cloning GEOFlow source..."
    git clone --depth=1 https://github.com/justmicos/GEOFlow.git kengine-src
}

# 2. Apply multi-provider & evolution patches
if (Test-Path "scripts/apply-patches.ps1") {
    Header "Applying GEOFlow patches"
    & .\scripts\apply-patches.ps1
}

# 3. Auto-detect local LLM engines
Header "Local LLM Detection"
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    Info "Ollama detected"
} else {
    Warn "Ollama not detected (optional — install from https://ollama.ai/)"
}

$lmStudioPath = "$env:LOCALAPPDATA\Programs\LM Studio"
if (Test-Path $lmStudioPath) {
    Info "LM Studio detected at $lmStudioPath"
} else {
    Warn "LM Studio not detected (optional)"
}

# 4. Create .env from example if missing
if (-not (Test-Path ".env")) {
    Header "Creating .env"
    Copy-Item ".env.example" ".env"
    Warn "Edit .env to set at least one AI provider API key:"
    Warn "  - DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
    Warn "  - Or set OLLAMA_BASE_URL for local inference"
}

# 5. Start services
Header "Starting Services"
docker compose up -d
Write-Host "GEOEngine at http://localhost:18080/geo_admin" -ForegroundColor $GREEN

Header "Next Steps"
Write-Host "  1. Open http://localhost:18080/geo_admin"
Write-Host "  2. Log in and configure AI models in Settings"
Write-Host "  3. Enable AI_GATEWAY_ENABLED=true in .env for auto-routing"
