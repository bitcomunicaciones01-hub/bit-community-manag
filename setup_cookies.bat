@echo off
chcp 65001
cd /d "%~dp0"
title SETUP COOKIES - BIT Community Manager
echo ====================================================
echo [SETUP] Configuración Manual de Sesión (Cookies)
echo ====================================================

python tools/import_cookies.py

pause
