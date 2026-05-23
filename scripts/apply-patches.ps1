# Apply GEOFlow patches — called by setup.ps1 after cloning kengine-src.
param(
    [string]$TargetDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "kengine-src")
)

$PatchesDir = Join-Path (Split-Path $PSScriptRoot -Parent) "patches"
$Green = "Green"; $Yellow = "Yellow"
function Info { Write-Host "[INFO]" -ForegroundColor $Green; Write-Host " $args" }
function Warn { Write-Host "[WARN]" -ForegroundColor $Yellow; Write-Host " $args" }

if (-not (Test-Path $TargetDir)) {
    Warn "kengine-src not found at $TargetDir. Run setup.ps1 first."
    exit 1
}

Info "Applying patches to kengine-src..."

# Copy PHP files
Get-ChildItem -Path $PatchesDir -Recurse -Filter "*.php" | ForEach-Object {
    $relativePath = $_.FullName.Substring($PatchesDir.Length + 1)
    $destPath = Join-Path $TargetDir $relativePath
    $destDir = Split-Path $destPath -Parent

    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $_.FullName $destPath -Force
    Info "Patched: $relativePath"
}

Info "Patches applied successfully."
