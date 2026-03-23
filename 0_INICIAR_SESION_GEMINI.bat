@echo off
setlocal

echo ====================================================
echo LOGIN DE GEMINI - BIT MANAGER
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
    echo [ERROR] No se encontro 'python' en el sistema. 
    echo Asegurate de tener Python instalado y en el PATH.
    goto end
)

echo [INFO] Iniciando script de captura...
echo Esto puede tardar unos segundos en abrir el bavegador...

python tools/gemini_login.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el script.
    echo Posibles causas: 
    echo 1. Playwright no esta instalado (corre: pip install playwright)
    echo 2. Los navegadores de Playwright no estan (corre: playwright install chrome)
    echo 3. Algun otro error de Python.
)

:end
echo.
echo ====================================================
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul
