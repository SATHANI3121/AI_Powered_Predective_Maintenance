@echo off
echo ============================================================
echo   AI-Powered Predictive Maintenance System
echo ============================================================
echo.
echo This will start the complete system:
echo   1. Database (Docker - optional)
echo   2. API Server (Port 8000)
echo   3. Upload training data
echo   4. Frontend Server (Port 3000)
echo.
echo Press any key to continue...
pause > nul

cd /d "%~dp0"

echo.
echo [1/5] Checking Docker (optional - will use SQLite if not available)...
docker ps >nul 2>&1
if %errorlevel% == 0 (
    echo Docker is running, starting PostgreSQL and Redis...
    docker-compose up -d db redis
    timeout /t 3 /nobreak > nul
) else (
    echo Docker not available - will use SQLite database
)

echo.
echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [3/5] Starting API server in background...
start "PDM API Server" cmd /k ".venv\Scripts\activate.bat && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

echo.
echo [4/5] Waiting for API server to start (10 seconds)...
timeout /t 10 /nobreak > nul

echo.
echo [5/5] Uploading training data...
python scripts\upload_data.py

echo.
echo ============================================================
echo   System Started Successfully!
echo ============================================================
echo.
echo   API Server: http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   Frontend:   Run start_frontend.bat to start the web interface
echo.
echo Press any key to start the frontend...
pause > nul

start "PDM Frontend" cmd /k "cd frontend && python server.py"

echo.
echo ============================================================
echo Both servers are now running!
echo Close the server windows to stop them.
echo ============================================================
pause

