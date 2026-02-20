@echo off
REM Investment Advisor - Price Update Runner (Every 24 hours)
REM Runs: price_fetcher -> update_portfolio -> evaluate
REM Double-click to run, or use with Task Scheduler.
REM In Task Scheduler: set "Start in" to C:\investment advisor

cd /d "C:\investment advisor"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\investment advisor\run_price_update.ps1"
exit /b %ERRORLEVEL%
