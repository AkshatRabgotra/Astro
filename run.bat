@echo off
echo ========================================================
echo   Starting Melooha AI Vedic Astrology Platform
echo ========================================================
start "Melooha Backend (FastAPI)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 /nobreak >nul
start "Melooha Frontend (Vite)" cmd /k "npm --prefix frontend run dev"
echo.
echo Both servers are running:
echo   - Frontend: http://localhost:5173
echo   - Backend:  http://127.0.0.1:8000
echo.
