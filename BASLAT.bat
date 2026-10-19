@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\KPSSIlanYakalayici\KPSS-Ilan-Yakalayici.exe" (
  start "" "%LOCALAPPDATA%\Programs\KPSSIlanYakalayici\KPSS-Ilan-Yakalayici.exe"
) else if exist "dist\KPSS-Ilan-Yakalayici\KPSS-Ilan-Yakalayici.exe" (
  start "" "dist\KPSS-Ilan-Yakalayici\KPSS-Ilan-Yakalayici.exe"
) else (
  start "" ".venv\Scripts\pythonw.exe" "main.py"
)
