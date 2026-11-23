@echo off
title Indian Stock AI Daily Automation
echo Running Autonomous Daily Indian Market Scan...
cd /d D:\STOCK_AI
"C:\Users\swamy.VISION\AppData\Local\Programs\Python\Python314\python.exe" scheduler.py --run-now

REM Ensure Live Sync Daemon is running in background (Port 5005)
powershell -NoProfile -Command "$c = Test-NetConnection -ComputerName 127.0.0.1 -Port 5005 -WarningAction SilentlyContinue; if (!$c.TcpTestSucceeded) { exit 1 } else { exit 0 }"
if %errorlevel% neq 0 (
    echo [INFO] Starting Live Sync Daemon on port 5005 in background...
    start "Indian Stock AI Live Sync Daemon" /min "C:\Users\swamy.VISION\AppData\Local\Programs\Python\Python314\python.exe" "D:\STOCK_AI\core\sync_server.py" --port 5005
)
