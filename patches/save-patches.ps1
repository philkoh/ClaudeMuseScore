$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
$MsDir = Join-Path $RepoDir "MuseScore"

Set-Location $MsDir

Get-ChildItem -Path $ScriptDir -Filter "[0-9]*.patch" | Remove-Item -ErrorAction SilentlyContinue

$diff = git diff
$diffCached = git diff --cached
if ([string]::IsNullOrEmpty($diff) -and [string]::IsNullOrEmpty($diffCached)) {
    Write-Host "No modifications to MuseScore source."
    exit 0
}

$outFile = Join-Path $ScriptDir "0001-custom-changes.patch"
git diff | Out-File -Encoding ascii $outFile
Write-Host "Saved patch: $outFile"
