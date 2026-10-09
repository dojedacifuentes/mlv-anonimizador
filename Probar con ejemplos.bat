@echo off
chcp 65001 >nul
setlocal
rem Tacha los 12 documentos ficticios de prueba y abre el informe y las carpetas para comparar.
set "RAIZ=%~dp0"
set "PYTHONIOENCODING=utf-8"
echo.
echo   Tachando los documentos de prueba (todos ficticios)...
echo.
"%RAIZ%.venv\Scripts\anonymize.exe" "%RAIZ%pruebas\archivos" --config "%RAIZ%paquete-chile\config-mlv.yaml" --format md,source --out-dir "%RAIZ%pruebas\tachados" -q
echo.
echo   Compruebo que no quede ningun dato a la vista...
"%RAIZ%.venv\Scripts\python.exe" "%RAIZ%pruebas\verificar_archivos.py"
start "" "%RAIZ%informe.html"
start "" "%RAIZ%pruebas\archivos"
start "" "%RAIZ%pruebas\tachados"
echo.
pause
