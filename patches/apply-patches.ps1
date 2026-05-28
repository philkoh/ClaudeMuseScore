$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir
$MsDir = Join-Path $RepoDir "MuseScore"

Set-Location $MsDir

$patches = Get-ChildItem -Path $ScriptDir -Filter "[0-9]*.patch" | Sort-Object Name

if ($patches.Count -eq 0) {
    Write-Host "No patches to apply."
    exit 0
}

foreach ($p in $patches) {
    Write-Host "Applying $($p.Name)..."
    git apply $p.FullName
}
Write-Host "All patches applied."
