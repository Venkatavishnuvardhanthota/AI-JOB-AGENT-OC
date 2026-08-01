param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
& (Join-Path $PSScriptRoot "scripts\launcher.ps1") restart @Arguments
exit $LASTEXITCODE
