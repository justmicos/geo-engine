$GREEN="Green"; $YELLOW="Yellow"
function Info { Write-Host "[INFO]" -ForegroundColor $GREEN; Write-Host " $args" }
function Warn { Write-Host "[WARN]" -ForegroundColor $YELLOW; Write-Host " $args" }
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) { Write-Host "[ERROR] Docker required"; exit 1 }
if (-not (Test-Path "kengine-src")) {
    Info "Cloning knowledge engine source..."
    git clone --depth=1 https://github.com/justmicos/GEOFlow.git kengine-src
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Warn "Edit .env to set AI_API_KEY"
}
Info "Starting services..."
docker compose up -d
Write-Host "GEOEngine at http://localhost:18080/geo_admin" -ForegroundColor $GREEN
