@echo off
title KDP Puzzle Book Generator
echo.
echo  =====================================================
echo   KDP Puzzle Book Generator
echo   Abriendo en: http://localhost:1771
echo  =====================================================
echo.

set PYTHON="C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe"

cd /d "%~dp0"

:: Abrir el navegador automaticamente
start "" http://localhost:1771

:: Iniciar el servidor
%PYTHON% app.py

pause
