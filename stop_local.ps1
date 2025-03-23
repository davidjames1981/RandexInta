# Stop Local Development Environment
Write-Host "Stopping CompactNodeInt Local Development Environment..." -ForegroundColor Yellow

# Function to stop a process
function Stop-ProcessByName {
    param($ProcessName)
    $process = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Stopping $ProcessName..." -ForegroundColor Yellow
        Stop-Process -Name $ProcessName -Force
    } else {
        Write-Host "$ProcessName is not running" -ForegroundColor Green
    }
}

# Stop Redis Server
Stop-ProcessByName "redis-server"

# Stop Celery Worker
Stop-ProcessByName "celery"

# Stop Django Server
Stop-ProcessByName "python"

Write-Host "`nAll services have been stopped!" -ForegroundColor Green 