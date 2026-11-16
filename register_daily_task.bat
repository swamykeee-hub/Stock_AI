@echo off
echo =================================================================
echo Registering Stock AI Daily Automation (Morning + 6:00 PM Evening)
echo =================================================================
echo.

echo 1. Creating Morning Scan Task (08:45 AM)...
schtasks /create /tn "IndianStockAI_MorningScan" /tr "\"D:\STOCK_AI\run_daily_scan.bat\"" /sc daily /st 08:45 /f

echo.
echo 2. Creating Evening Scan Task (06:00 PM / 18:00)...
schtasks /create /tn "IndianStockAI_EveningScan" /tr "\"D:\STOCK_AI\run_daily_scan.bat\"" /sc daily /st 18:00 /f

echo.
echo =================================================================
echo SUCCESS: Both Morning (08:45 AM) and Evening (06:00 PM) tasks
echo have been registered into Windows Task Scheduler!
echo They will run automatically every day in the background.
echo =================================================================
pause
