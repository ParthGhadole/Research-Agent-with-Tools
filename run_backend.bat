@echo off
title FastAPI Backend
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

:: Run the API
echo Starting FastAPI on port 8000...
uv run uvicorn src.api.routes:fastapi_app --host 0.0.0.0 --port 8000 --workers 4

pause