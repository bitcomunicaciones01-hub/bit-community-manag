@echo off
chcp 65001
cd /d "%~dp0"
title LOGIN INSTAGRAM - BIT Community Manager
echo ====================================================
echo [LOGIN] Herramienta de Inicio de Sesión Interactivo
echo Úsala cuando el bot diga "ChallengeRequired" o falle al publicar.
echo ====================================================

python tools/interactive_login.py

pause
