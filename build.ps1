$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& "$PSScriptRoot/.venv/Scripts/python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name KPSS-Ilan-Yakalayici --collect-all rapidocr_onnxruntime --collect-all onnxruntime --hidden-import pystray._win32 main.py
if ($LASTEXITCODE -ne 0) { throw 'EXE oluşturulamadı.' }
