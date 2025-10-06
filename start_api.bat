@echo off
echo ============================================================
echo   Starting API Server
echo ============================================================
echo.

cd /d "%~dp0"

echo Checking Docker (optional)...
docker ps >nul 2>&1
if %errorlevel% == 0 (
    echo Docker is running, starting database services...
    docker-compose up -d db redis
    timeout /t 3 /nobreak > nul
    echo.
) else (
    echo Docker not available - using SQLite database
    echo.
)

call .venv\Scripts\activate.bat

echo Starting API server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause

