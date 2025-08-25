@echo off
title Job Automation System - Production
echo.
echo ========================================
echo   JOB AUTOMATION SYSTEM - PRODUCTION
echo ========================================
echo.
echo Starting automation system...
echo This will run the complete automation:
echo - Fetch jobs from APIs
echo - Process and filter jobs
echo - Generate captions
echo - Post to LinkedIn
echo - Run continuously
echo.
echo Press Ctrl+C to stop the system
echo.
echo ========================================
echo.

python run_automation.py

echo.
echo ========================================
echo Automation system stopped.
echo Check logs/automation.log for details.
echo ========================================
pause

