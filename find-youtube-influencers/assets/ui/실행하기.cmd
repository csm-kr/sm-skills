@echo off
chcp 65001 >nul
title YouTube 인플루언서 파인더
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-ui.ps1"
if errorlevel 1 pause
