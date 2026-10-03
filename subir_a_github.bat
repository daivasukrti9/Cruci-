@echo off
echo ========================================================
echo Preparando repositorio y subiendo a GitHub...
echo ========================================================

:: Añadir todos los archivos
git add .

:: Confirmar cambios
set /p commit_msg="Introduce el mensaje de commit (ej. 'Agregado prompt de emergent'): "
if "%commit_msg%"=="" set commit_msg="Auto-commit: Progreso Cruci y Prompt Emergent"
git commit -m "%commit_msg%"

:: Asegurar que la rama principal es 'main' o 'master' (por defecto git usa master, GitHub prefiere main)
git branch -M main

:: Preguntar por la URL del repositorio remoto si no existe
git remote -v | find "daivasukrti9" >nul
if errorlevel 1 (
    echo.
    echo No tienes un remoto configurado para 'daivasukrti9'.
    echo Por favor crea un repositorio vacío en github.com/daivasukrti9 llamado 'Cruci'.
    set /p repourl="Ingresa la URL del repo (ej. https://github.com/daivasukrti9/Cruci.git): "
    git remote add origin %repourl%
)

:: Subir cambios
echo Subiendo a GitHub...
git push -u origin main

echo.
echo ========================================================
echo Subida finalizada. Presiona cualquier tecla para salir.
echo ========================================================
pause
