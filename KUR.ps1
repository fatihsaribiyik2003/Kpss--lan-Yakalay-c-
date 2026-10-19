param([switch]$NoStart)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'dist/KPSS-Ilan-Yakalayici'
$target = Join-Path $env:LOCALAPPDATA 'Programs/KPSSIlanYakalayici'
$app = Join-Path $target 'KPSS-Ilan-Yakalayici.exe'
if (-not (Test-Path -LiteralPath (Join-Path $source 'KPSS-Ilan-Yakalayici.exe'))) {
    throw 'Hazır uygulama paketi bulunamadı. Önce build.ps1 çalıştırılmalı.'
}
New-Item -ItemType Directory -Path $target -Force | Out-Null
Get-ChildItem -LiteralPath $source | Copy-Item -Destination $target -Recurse -Force
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
foreach ($shortcutPath in @((Join-Path $desktop 'KPSS İlan Yakalayıcı.lnk'), (Join-Path $PSScriptRoot 'İlan Yakalayıcı.lnk'))) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $app
    $shortcut.WorkingDirectory = $target
    $shortcut.Description = 'Resmî Gazete otomatik PDF ve OCR takibi'
    $shortcut.Save()
}
if (-not $NoStart) {
    Start-Process -FilePath $app -WorkingDirectory $target -WindowStyle Hidden
}
Write-Output "Kuruldu: $app"
