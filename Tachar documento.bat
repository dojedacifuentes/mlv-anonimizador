@echo off
chcp 65001 >nul
setlocal
title Anonimizador Jurídico MLV
rem Arrastra PDF o Word sobre este archivo, o haz doble clic para elegirlos.
set "RAIZ=%~dp0"
set "PY=%RAIZ%.venv\Scripts\python.exe"
set "PYTHONIOENCODING=utf-8"
if exist "%RAIZ%.ultima-salida" del "%RAIZ%.ultima-salida"

echo.
echo   ANONIMIZADOR JURÍDICO MLV  ·  prueba de concepto
echo   Todo ocurre en este computador. No se envía nada a internet.
echo.

if "%~1"=="" (
  set "LISTA=%TEMP%\mlv-elegidos.txt"
  powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Elige los documentos que quieres tachar'; $d.Filter = 'PDF, Word o texto (*.pdf;*.docx;*.txt;*.md)|*.pdf;*.docx;*.txt;*.md'; $d.Multiselect = $true; if ($d.ShowDialog() -eq 'OK') { $d.FileNames | Set-Content -Encoding UTF8 $env:TEMP\mlv-elegidos.txt } else { '' | Set-Content $env:TEMP\mlv-elegidos.txt }"
  setlocal enabledelayedexpansion
  set "ARGS="
  for /f "usebackq delims=" %%F in ("%TEMP%\mlv-elegidos.txt") do if not "%%F"=="" set ARGS=!ARGS! "%%F"
  if "!ARGS!"=="" ( echo   No elegiste ningún documento. & echo. & pause & exit /b )
  echo   Tachando… el primer documento tarda unos segundos.
  echo.
  "%PY%" "%RAIZ%herramientas\tachar.py" !ARGS!
  endlocal
) else (
  echo   Tachando… el primer documento tarda unos segundos.
  echo.
  "%PY%" "%RAIZ%herramientas\tachar.py" %*
)

if exist "%RAIZ%.ultima-salida" (
  set /p CARPETA=<"%RAIZ%.ultima-salida"
  echo.
  echo   Revisa siempre el resultado antes de usarlo.
  call start "" "%%CARPETA%%"
)
echo.
pause
