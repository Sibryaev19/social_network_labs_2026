@echo off
rem Запуск лабораторной 1 на Windows
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python setup\setup.py
    if errorlevel 1 exit /b 1
)

.venv\Scripts\python.exe start.py %*
