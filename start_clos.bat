@echo off
echo ============================================================
echo CLOS Incubator v0.5 - STARTING
echo ============================================================

cd /d C:\Users\48661\Desktop\SST-Incubator

echo.
echo [1] Starting Studio UI...
start "CLOS Studio" cmd /k "streamlit run clos_tower/ui/studio.py --server.port 8502 --server.headless true"

echo [2] Starting API Server...
start "CLOS API" cmd /k "uvicorn clos_tower.app:app --host 127.0.0.1 --port 8000"

echo.
echo ============================================================
echo CLOS Incubator is running!
echo.
echo Studio UI:  http://localhost:8502
echo API:        http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo.
echo Close this window, keep the other two open.
echo ============================================================
pause
