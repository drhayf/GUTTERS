@echo off
echo ========================================================
echo   GUTTERS SYSTEM LAUNCHER
echo ========================================================
echo.
echo Launching services in separate windows...

:: 1. Start Node.js Push Service (Port 4000)
echo Starting Push Service...
start "GUTTERS Push Service (Node)" cmd /k "cd push-service && npm run dev"

:: 2. Start Python Backend (Port 8000)
echo Starting Backend API...
start "GUTTERS API (Python)" cmd /k "uvicorn src.app.main:app --reload --port 8000"

:: 3. Start Python Worker (ARQ)
echo Starting Worker...
start "GUTTERS Worker (ARQ)" cmd /k "arq src.app.worker.WorkerSettings --watch src"

:: 4. Start Frontend (Vite)
echo Starting Frontend...
start "GUTTERS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo   SYSTEM LAUNCHED
echo ========================================================
echo   - Push Service: http://localhost:4000
echo   - Backend API:  http://localhost:8000
echo   - Frontend:     http://localhost:5173 (usually)
echo.
echo   Press any key to exit this launcher (services will stay open)...
pause
exit
