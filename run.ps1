param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
& (Join-Path $PSScriptRoot "scripts\launcher.ps1") start @Arguments
exit $LASTEXITCODE
