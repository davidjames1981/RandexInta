# startup.ps1

Write-Host "`n=== Starting Randex Integration Services ===`n" -ForegroundColor Cyan

# Kill any existing processes
Write-Host "Stopping existing processes..." -ForegroundColor Yellow
taskkill /F /IM redis-server.exe 2>$null
taskkill /F /IM celery.exe 2>$null
taskkill /F /IM python.exe 2>$null
Start-Sleep -Seconds 2

# Delete celerybeat schedule file
Write-Host "Cleaning up celerybeat schedule..." -ForegroundColor Yellow
Remove-Item celerybeat-schedule -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Create logs directory if it doesn't exist
Write-Host "Checking log directory..." -ForegroundColor Yellow
$logPath = "C:\Cursor\RandexInt\Files\logs"
if (-not (Test-Path $logPath)) {
    New-Item -ItemType Directory -Path $logPath -Force
}

# Start Redis Server
Write-Host "`nStarting Redis Server..." -ForegroundColor Green
Start-Process "C:\Redis\redis-server.exe" -WindowStyle Minimized
Start-Sleep -Seconds 3

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start Celery worker in a new window
Write-Host "Starting Celery Worker..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; python manage.py celery_local"

# Start Celery beat in a new window
Write-Host "Starting Celery Beat..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; python manage.py celerybeat_local"

# Start Django development server in a new window
Write-Host "Starting Django Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; python manage.py runserver"

Write-Host "`n=== All services started ===`n" -ForegroundColor Cyan
Write-Host "Services running:" -ForegroundColor Green
Write-Host "1. Redis Server - redis-server.exe"
Write-Host "2. Celery Worker - celery worker"
Write-Host "3. Celery Beat - celery beat"
Write-Host "4. Django Server - python manage.py runserver"
Write-Host "`nWeb interface available at: http://localhost:8000`n"