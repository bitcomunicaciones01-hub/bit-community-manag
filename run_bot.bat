@echo off
chcp 65001
cd /d "%~dp0"
title BIT Community Manager - DO NOT CLOSE

:loop
cls
echo ====================================================
echo [BOOT] Iniciando Community Manager Bot...
echo [TIME] %DATE% %TIME%
echo ====================================================

:: Verificar si python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instala Python y agregalo al PATH.
    pause
    exit /b
)

:: Ejecutar el bot
echo [RUN] Ejecutando main.py...
python main.py

:: Si el bot se cierra, esperar y reiniciar
echo.
echo [WARNING] El bot se ha detenido. Reiniciando en 10 segundos...
echo Presiona Ctrl+C para detener el ciclo.
timeout /t 10
goto loop
