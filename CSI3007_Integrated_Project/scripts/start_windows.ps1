# CSI3007 Integrated Project - start script (PowerShell)
# Starts the three APIs, the integration gateway (landing page) and the three
# Streamlit dashboards. Press Ctrl+C to stop all services.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)   # repository root

$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

& $python start_all.py @args
