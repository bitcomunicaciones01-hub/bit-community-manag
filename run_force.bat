@echo off
chcp 65001
cd /d "%~dp0"
title Force Run Job - BIT Community Manager
echo ====================================================
echo [FORCE] Forzando ejecución del trabajo de publicación...
echo [TIME] %DATE% %TIME%
echo ====================================================

python tools/force_run_job.py

echo.
echo ====================================================
echo [DONE] Proceso finalizado.
echo ====================================================
pause
