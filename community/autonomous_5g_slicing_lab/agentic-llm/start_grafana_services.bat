@echo off
echo Starting Grafana and InfluxDB services...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Stop any existing containers
echo Stopping existing containers...
docker-compose down

REM Start services
echo Starting services...
docker-compose up -d

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo Failed to start services. Check the logs with: docker-compose logs
    pause
    exit /b 1
) else (
    echo ✅ Services started successfully!
    echo 📊 Grafana is available at: http://localhost:3000
    echo    Username: admin
    echo    Password: admin
    echo 📈 InfluxDB is available at: http://localhost:8086
    echo.
    echo 🚀 You can now run the Streamlit app with Grafana integration!
)

pause 