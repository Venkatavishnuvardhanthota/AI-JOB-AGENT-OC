param(
    [switch]$NoBuild,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
$rootDir = $PSScriptRoot
$backendEnv = Join-Path $rootDir "backend\.env"
$backendEnvExample = Join-Path $rootDir "backend\.env.example"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Job Agent V2 - Startup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Validate environment
Write-Host "[1/7] Validating environment..." -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $backendEnv)) {
    Write-Host "  backend/.env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item $backendEnvExample $backendEnv
    Write-Host "  Created backend/.env - please review and configure." -ForegroundColor Green
}

# Read current APP_SECRET_KEY
$envContent = Get-Content $backendEnv -Raw
$secretKey = [System.Text.RegularExpressions.Regex]::Match($envContent, 'APP_SECRET_KEY=(.+)').Groups[1].Value.Trim()

if (-not $secretKey -or $secretKey -eq 'change-me-to-a-secure-random-key') {
    Write-Host "  WARNING: APP_SECRET_KEY is not set or is the default value." -ForegroundColor Yellow
    Write-Host "  Generating a secure random key..." -ForegroundColor Yellow
    $newKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
    $envContent = $envContent -replace 'APP_SECRET_KEY=.*', "APP_SECRET_KEY=$newKey"
    Set-Content $backendEnv $envContent
    Write-Host "  APP_SECRET_KEY generated and saved." -ForegroundColor Green
}

Write-Host "  Environment OK" -ForegroundColor Green

# Step 2: Stop old containers
Write-Host "[2/7] Stopping old containers..." -ForegroundColor Yellow
docker compose down --remove-orphans 2>$null
Write-Host "  Old containers stopped." -ForegroundColor Green

# Step 3: Build and start containers
Write-Host "[3/7] Starting services..." -ForegroundColor Yellow
Push-Location $rootDir
if ($NoBuild) {
    docker compose up -d
} else {
    docker compose up --build -d
}
Pop-Location
Write-Host "  Services started." -ForegroundColor Green

# Step 4: Wait for database
Write-Host "[4/7] Waiting for database..." -ForegroundColor Yellow
$dbReady = $false
for ($i = 0; $i -lt 30; $i++) {
    $result = docker exec aja-db pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        $dbReady = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $dbReady) {
    Write-Host "ERROR: Database failed to start within 60 seconds." -ForegroundColor Red
    exit 1
}
Write-Host "  Database ready." -ForegroundColor Green

# Step 5: Wait for backend health
Write-Host "[5/7] Waiting for backend..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Not ready yet
    }
    Start-Sleep -Seconds 2
}
if (-not $backendReady) {
    Write-Host "ERROR: Backend failed to start within 60 seconds." -ForegroundColor Red
    Write-Host "Run 'docker logs aja-backend' for details." -ForegroundColor Yellow
    exit 1
}
Write-Host "  Backend healthy." -ForegroundColor Green

# Step 6: Detect and run pending migrations
Write-Host "[6/7] Checking migrations..." -ForegroundColor Yellow
$migrationOutput = docker exec aja-backend alembic upgrade head 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Migrations up to date." -ForegroundColor Green
} else {
    Write-Host "  Migration warning (may be first run): $migrationOutput" -ForegroundColor Yellow
}

# Step 7: Open application
Write-Host "[7/7] Ready!" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AI Job Agent V2 is running" -ForegroundColor Cyan
Write-Host "                                               " -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health:   http://localhost:8000/health" -ForegroundColor White
Write-Host "                                               " -ForegroundColor Cyan
Write-Host "   Register a new account to get started." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $NoOpen) {
    Start-Process "http://localhost"
}
