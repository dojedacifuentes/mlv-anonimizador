@echo off
chcp 65001 >nul
setlocal
rem Anonimizador Juridico MLV (prueba): arrastra PDF o Word sobre este archivo, o haz doble clic para elegirlos.
set "RAIZ=%~dp0"
set "PROGRAMA=%RAIZ%.venv\Scripts\anonymize.exe"
set "CONFIG=%RAIZ%paquete-chile\config-mlv.yaml"
set "PYTHONIOENCODING=utf-8"
set "ULTIMA="

echo.
echo   ANONIMIZADOR JURIDICO MLV  ·  prueba de concepto
echo   Todo ocurre en este computador. No se envia nada a internet.
echo.

if "%~1"=="" (
  for /f "usebackq delims=" %%F in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Elige los documentos que quieres tachar'; $d.Filter = 'PDF, Word o texto (*.pdf;*.docx;*.txt;*.md)|*.pdf;*.docx;*.txt;*.md'; $d.Multiselect = $true; if ($d.ShowDialog() -eq 'OK') { $d.FileNames }"`) do call :tachar "%%F"
) else (
  for %%F in (%*) do call :tachar "%%~F"
)

if defined ULTIMA (
  echo.
  echo   Listo. Abro la carpeta «Tachados». Revisa siempre el resultado antes de usarlo.
  start "" "%ULTIMA%"
) else (
  echo   No elegiste ningun documento.
)
echo.
pause
exit /b

:tachar
set "SALIDA=%~dp1Tachados"
echo   Tachando: %~nx1
"%PROGRAMA%" "%~1" --config "%CONFIG%" --format md,source --out-dir "%SALIDA%" -q
if errorlevel 1 (
  echo   [!] No se pudo tachar %~nx1
) else (
  set "ULTIMA=%SALIDA%"
)
echo.
exit /b
