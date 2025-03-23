# Start Local Development Environment
Write-Host "Starting CompactNodeInt Local Development Environment..." -ForegroundColor Green

# Function to check if a process is running
function Test-ProcessRunning {
    param($ProcessName)
    return Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
}

# Function to start a process in a new window
function Start-ProcessInNewWindow {
    param(
        [string]$Command,
        [string]$WindowTitle
    )
    # Create a script that sets the window title and runs the command
    $scriptBlock = "
        `$host.ui.RawUI.WindowTitle = '$WindowTitle'
        $Command
    "
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock -WindowStyle Normal
}

# Check if Redis is running
if (-not (Test-ProcessRunning "redis-server")) {
    Write-Host "Starting Redis Server..." -ForegroundColor Yellow
    Start-ProcessInNewWindow "C:\Redis\redis-server.exe" "Redis Server"
    Start-Sleep -Seconds 2  # Wait for Redis to start
} else {
    Write-Host "Redis Server is already running" -ForegroundColor Green
}

# Activate virtual environment and set environment variables
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "Virtual environment not found. Please create it first." -ForegroundColor Red
    exit 1
}

# Create commands that include virtual environment activation
$activateAndRun = ". '$venvPath';"

# Start Celery Worker
Write-Host "Starting Celery Worker..." -ForegroundColor Yellow
Start-ProcessInNewWindow ($activateAndRun + "celery -A CompactNodeInt worker --pool=solo -l info") "Celery Worker"

# Start Celery Beat
Write-Host "Starting Celery Beat..." -ForegroundColor Yellow
Start-ProcessInNewWindow ($activateAndRun + "celery -A CompactNodeInt beat -l info") "Celery Beat"

# Start Django Development Server
Write-Host "Starting Django Development Server..." -ForegroundColor Yellow
Start-ProcessInNewWindow ($activateAndRun + "python manage.py runserver") "Django Server"

Write-Host "`nAll services have been started!" -ForegroundColor Green
Write-Host "You can access the application at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C in each window to stop the respective service." -ForegroundColor Yellow 