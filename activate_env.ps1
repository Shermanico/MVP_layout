# Activate Python virtual environment for Multi-Drone Coordination System
# Note: This script must be executed with: . .\activate_env.ps1 (note the dot at the beginning)
# Or use: & .\activate_env.ps1

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To deactivate, type: deactivate" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

