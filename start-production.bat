@echo off
echo ========================================
echo  Automated Lead Engine - Production Start
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Starting Docker containers...
cd backend
docker-compose up -d --build

echo.
echo [2/4] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [3/4] Checking API health...
curl -s http://localhost:8000/ >nul
if errorlevel 1 (
    echo WARNING: API may not be ready yet. Check docker-compose logs.
) else (
    echo API is running!
)

echo.
echo [4/4] Starting frontend...
cd ..
start cmd /k "npm run dev"

echo.
echo ========================================
echo  All services started!
echo ========================================
echo.
echo  Dashboard:    http://localhost:3000
echo  API:          http://localhost:8000
echo  API Docs:     http://localhost:8000/docs
echo  Demo Sites:   http://localhost:8000/demo-sites/
echo.
echo  To view logs: docker-compose logs -f
echo  To stop:      docker-compose down
echo.
pause
