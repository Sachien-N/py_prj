# CSI3007 Integrated Project - Windows setup script (PowerShell)
# Course: CSI3007 Advanced Python Programming
# Run from the repository root:  powershell -ExecutionPolicy Bypass -File scripts/setup_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== CSI3007 Integrated Project - Windows setup ===" -ForegroundColor Cyan

# 1. Python check
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python was not found. Install Python 3.11+ from https://www.python.org/downloads/ and re-run." -ForegroundColor Red
    exit 1
}
$version = (& python --version) 2>&1
Write-Host "Found $version"

# 2. Virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: .venv\Scripts\python.exe not found after creation." -ForegroundColor Red
    exit 1
}

# 3. Dependencies
Write-Host "Installing pinned dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

# 4. Per-project .env files from templates (idempotent)
$projects = @(
    "person_a_sachien_n_23MID0255",
    "person_b_shravan_n_a_23MID0445",
    "person_c_hariharan_s_23MID0182"
)
foreach ($project in $projects) {
    $example = Join-Path $project ".env.example"
    $target  = Join-Path $project ".env"
    if ((Test-Path $example) -and -not (Test-Path $target)) {
        Copy-Item $example $target
        Write-Host "Created $target from template"
    }
}

# 5. Root .env for the gateway (optional)
if ((Test-Path ".env.example") -and -not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created root .env from template"
}

# 6. Syntax sanity check
Write-Host "Verifying Python syntax of all project modules..."
& $venvPython -m compileall -q person_a_sachien_n_23MID0255 person_b_shravan_n_a_23MID0445 person_c_hariharan_s_23MID0182 integration shared
if ($LASTEXITCODE -eq 0) { Write-Host "Syntax OK" -ForegroundColor Green }

Write-Host ""
Write-Host "Setup complete. Start everything with:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\python.exe start_all.py"
Write-Host "or use scripts\start_windows.ps1"
