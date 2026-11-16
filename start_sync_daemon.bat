@echo off
title Indian Stock AI Live Sync Daemon
echo ===================================================
echo Indian Stock AI Live Sync Daemon (Port 5005)
echo Real-Time NSE CMP Quotes & Auto-Refresh Server
echo ===================================================
cd /d D:\STOCK_AI
"C:\Users\swamy.VISION\AppData\Local\Programs\Python\Python314\python.exe" core\sync_server.py --port 5005
pause
