Write-Host "========================================================" -ForegroundColor Magenta
Write-Host "  Starting Melooha AI Vedic Astrology Platform" -ForegroundColor Magenta
Write-Host "========================================================" -ForegroundColor Magenta

# Launch backend in separate PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

# Brief pause before launching frontend
Start-Sleep -Seconds 2

# Launch frontend in separate PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm --prefix frontend run dev"

Write-Host ""
Write-Host "Both servers launched successfully!" -ForegroundColor Green
Write-Host "  Frontend App: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Backend API:  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
