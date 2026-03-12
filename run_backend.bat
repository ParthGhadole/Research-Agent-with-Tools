@echo off
title FastAPI Server
echo Starting FastAPI backend on port 8000...
uv run uvicorn src.api.routes:fastapi_app --host 0.0.0.0 --port 8000 --workers 4
pause