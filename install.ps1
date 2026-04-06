# =============================================================================
# Singularity Works Forge — One-Touch Installer (Windows PowerShell)
# Requires: Python 3.11+, git, PowerShell 5+
# Run: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#      .\install.ps1
# =============================================================================
param(
    [string]$InstallDir = "$env:USERPROFILE\.singularity-works"
)
$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/SEng-Kitathas/Singularity-works-.git"

function Write-Step  { Write-Host "`n── $args ──" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "~ $args" -ForegroundColor Yellow }
function Write-Fail  { Write-Host "✗ ERROR: $args" -ForegroundColor Red; exit 1 }

Write-Host @"
  ╔══════════════════════════════════════════════════╗
  ║   SINGULARITY WORKS FORGE — Installer v1.0      ║
  ║   Bug Bounty Engine · Security Analysis Forge    ║
  ╚══════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# ── 1. Python check ───────────────────────────────────────────────────────────
Write-Step "Checking Python"
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { Write-Fail "Python not found. Install from https://python.org (3.11+)" }
$ver = & $py.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$ok  = & $py.Source -c "import sys; print('ok' if sys.version_info >= (3,11) else 'fail')"
if ($ok -ne "ok") { Write-Fail "Python 3.11+ required, found $ver" }
Write-Ok "Python $ver"
$PyExe = $py.Source

# ── 2. Git check ──────────────────────────────────────────────────────────────
Write-Step "Checking git"
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { Write-Fail "git not found. Install from https://git-scm.com" }
Write-Ok "git $(git --version)"

# ── 3. Clone / update ─────────────────────────────────────────────────────────
Write-Step "Installing forge"
if (Test-Path "$InstallDir\.git") {
    Write-Host "· Existing install at $InstallDir — updating"
    Push-Location $InstallDir
    git pull --ff-only origin main
    $sha = git rev-parse --short HEAD
    Write-Ok "Updated to $sha"
    Pop-Location
} else {
    Write-Host "· Cloning to $InstallDir"
    git clone $RepoUrl $InstallDir
    Push-Location $InstallDir
    $sha = git rev-parse --short HEAD
    Write-Ok "Cloned $sha"
    Pop-Location
}

# ── 4. Virtual environment ────────────────────────────────────────────────────
Write-Step "Setting up Python environment"
$VenvDir = "$InstallDir\.venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "· Creating venv"
    & $PyExe -m venv $VenvDir
}
$VenvPy = "$VenvDir\Scripts\python.exe"
Write-Ok "venv: $VenvDir"

# ── 5. Dependencies ───────────────────────────────────────────────────────────
Write-Step "Installing dependencies"
& $VenvPy -m pip install --quiet --upgrade pip wheel
& $VenvPy -m pip install --quiet `
    "flask>=3.0" "flask-cors>=4.0" "flask-socketio>=5.3" `
    "mcp>=0.9" "watchdog>=3.0"
Write-Ok "Dependencies installed"
& $VenvPy -m pip install --quiet "rich>=13.0" 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "rich installed" } else { Write-Warn "rich optional" }

# ── 6. Install package ────────────────────────────────────────────────────────
Write-Step "Installing Singularity Works package"
Push-Location $InstallDir
& $VenvPy -m pip install --quiet -e .
Pop-Location
Write-Ok "singularity-works installed"

# ── 7. Verify ─────────────────────────────────────────────────────────────────
Write-Step "Verifying installation"
$verify = @"
import sys
sys.path.insert(0, r'$InstallDir')
from singularity_works.orchestration import Orchestrator
from singularity_works.hud import ConsoleHUD
from singularity_works.bounty_reporter import build_report
from singularity_works.local_model_adapter import LocalModelAdapter
print('  forge core:      OK')
print('  hud v3:          OK')
print('  bounty reporter: OK')
print('  model adapter:   OK')
"@
& $VenvPy -c $verify
Write-Ok "All forge modules verified"

# ── 8. Write launcher scripts ─────────────────────────────────────────────────
Write-Step "Writing launchers"
$forge_ps1 = @"
`$VenvPy = '$VenvDir\Scripts\python.exe'
Push-Location '$InstallDir'
& `$VenvPy -m singularity_works.bounty_reporter @args
Pop-Location
"@
Set-Content -Path "$InstallDir\forge.ps1" -Value $forge_ps1
Write-Ok "forge.ps1 → $InstallDir\forge.ps1"

$health_ps1 = @"
`$VenvPy = '$VenvDir\Scripts\python.exe'
Push-Location '$InstallDir'
& `$VenvPy -m singularity_works.local_model_adapter health @args
Pop-Location
"@
Set-Content -Path "$InstallDir\forge-health.ps1" -Value $health_ps1
Write-Ok "forge-health.ps1 → $InstallDir\forge-health.ps1"

# ── 9. Claude Code MCP config ────────────────────────────────────────────────
Write-Step "Claude Code MCP configuration"
$McpJson = @"
{
  "mcpServers": {
    "singularity-works": {
      "command": "$VenvDir\Scripts\python.exe",
      "args": ["$InstallDir\singularity_works\forge_mcp_server.py"],
      "cwd": "$InstallDir"
    }
  }
}
"@
$ClaudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $ClaudeDir)) { New-Item -ItemType Directory $ClaudeDir | Out-Null }
Set-Content -Path "$ClaudeDir\mcp_singularity_works.json" -Value $McpJson
Write-Ok "MCP config → $ClaudeDir\mcp_singularity_works.json"

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Singularity Works Forge installed." -ForegroundColor Green
Write-Host "══════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Install dir: $InstallDir"
Write-Host ""
Write-Host "  Quick start:"
Write-Host "    # Check LM Studio models" -ForegroundColor Yellow
Write-Host "    .\forge-health.ps1"
Write-Host ""
Write-Host "    # Scan a file" -ForegroundColor Yellow
Write-Host "    .\forge.ps1 path\to\app.py --platform HackerOne --out .\reports"
Write-Host ""
Write-Host "    # Claude Code MCP config:" -ForegroundColor Yellow
Write-Host "    cat $ClaudeDir\mcp_singularity_works.json"
Write-Host ""
