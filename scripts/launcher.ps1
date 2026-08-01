param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot "launcher.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $launcher $Command @Arguments
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $launcher $Command @Arguments
} else {
    Write-Host "Python 3 is required by the AI Job Agent launcher." -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/, then run this command again." -ForegroundColor Yellow
    exit 2
}

exit $LASTEXITCODE
