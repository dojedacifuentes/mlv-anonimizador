@echo off
chcp 65001 >nul
setlocal
title Anonimizador Jurídico MLV · ejemplos
rem Tacha los 12 documentos FICTICIOS de prueba y abre el informe y las carpetas para comparar.
set "RAIZ=%~dp0"
set "PYTHONIOENCODING=utf-8"
echo.
echo   PRUEBA CON EJEMPLOS  ·  6 documentos ficticios, en PDF y en Word
echo   (contrato, informe Ley Karin, demanda, compraventa, finiquito, mediación)
echo.
"%RAIZ%.venv\Scripts\python.exe" "%RAIZ%herramientas\tachar.py" "%RAIZ%pruebas\archivos" --salida "%RAIZ%pruebas\tachados"
echo.
echo   Ahora compruebo, archivo por archivo, que no quede ningún dato a la vista:
echo.
"%RAIZ%.venv\Scripts\python.exe" "%RAIZ%pruebas\verificar_archivos.py"
start "" "%RAIZ%informe.html"
start "" "%RAIZ%pruebas\archivos"
start "" "%RAIZ%pruebas\tachados"
echo.
echo   Se abrieron el informe y las carpetas de antes (archivos) y después (tachados).
echo.
pause
