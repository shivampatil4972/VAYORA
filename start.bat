@echo off
echo ============================================================
echo Starting VAYORA Platform
echo ============================================================

REM Check if docker-compose is available
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo docker-compose not found. Please install Docker Desktop.
    exit /b 1
)

echo Pulling latest images...
docker-compose pull

echo Building and starting containers in detached mode...
docker-compose up -d --build

echo.
echo ============================================================
echo VAYORA is now running!
echo ============================================================
echo - Frontend:        http://localhost:5173
echo - Spring Backend:  http://localhost:8080/api/auth/health
echo - AI Service:      http://localhost:8000/health
echo - Realtime Gateway:http://localhost:3001/health
echo.
echo To view logs, run: docker-compose logs -f
echo To stop services, run: docker-compose down
echo ============================================================
