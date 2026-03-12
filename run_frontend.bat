@echo off
title Streamlit Frontend
setlocal

:: Verify uv is installed globally
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 'uv' is not installed. Please run: pip install uv
    pause
    exit /b
)

:: Notify only if the environment is missing entirely
if not exist ".venv" (
    echo [INFO] Virtual environment not found. Performing initial setup...
)

:: Always run sync to verify/repair the environment
uv sync

:: Run the app
echo Starting Streamlit...
uv run streamlit run app/app.py

pause