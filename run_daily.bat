@echo off
REM Investment Advisor - Scheduled Runner (Every 72 hours)
REM Double-click to run, or use with Task Scheduler

powershell -ExecutionPolicy Bypass -File "C:\investment advisor\run_daily.ps1"

