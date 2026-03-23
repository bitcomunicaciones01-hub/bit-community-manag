@echo off
setlocal
chcp 65001 > nul

echo ====================================================
echo 🔐 INICIADOR DE SESIÓN GEMINI - BIT MANAGER
echo ====================================================

:: Cambiar al directorio del script
cd /d "%~dp0"
echo Directorio actual: %cd%

:: Asegurar que existe la carpeta brain
if not exist "brain" (
    echo [INFO] Creando carpeta brain...
    mkdir "brain"
)

:: Comprobar si python existe
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encontró 'python' en el sistema. 
    echo Asegúrate de tener Python instalado y en el PATH.
    goto end
)

echo [INFO] Iniciando script de captura...
echo ⏳ Esto puede tardar unos segundos en abrir el navegador...

python tools/gemini_login.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el script.
    echo Posibles causas: 
    echo 1. Playwright no está instalado (corré: pip install playwright)
    echo 2. Los navegadores de Playwright no están (corré: playwright install chrome)
    echo 3. Algún otro error de Python.
)

:end
echo.
echo ====================================================
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul
