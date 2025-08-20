@echo off
echo 🚀 Job Automation Application
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ⚠️  Virtual environment not found
    echo    Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist "venv\Lib\site-packages\requests" (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found
    echo    Please create .env file with your API keys
    echo    Copy env.template to .env and edit it
    echo.
)

REM Check if config.yaml exists
if not exist "config.yaml" (
    echo ❌ config.yaml not found
    echo    This file is required
    pause
    exit /b 1
)

REM Check if database is initialized
if not exist "job_automation.db" (
    echo ℹ️  Database not initialized
    echo    Run: python cli.py init
    echo.
)

echo 📋 Available commands:
echo    python cli.py init          # Initialize database
echo    python cli.py status        # Check system status
echo    python cli.py fetch         # Manually fetch jobs
echo    python cli.py post          # Manually post content
echo    python cli.py start         # Start automated mode
echo    python test_system.py       # Run system tests
echo    python test_gemini.py       # Test Gemini API integration
echo    python setup_mysql.py       # Setup MySQL database
echo    python migrate_to_mysql.py  # Migrate from SQLite to MySQL
echo.

echo 🔧 Quick start:
echo    1. python cli.py init       # Initialize database
echo    2. python cli.py status     # Verify system status
echo    3. python cli.py start      # Start automation
echo.

echo 📚 For more information, see README.md
echo ========================================
echo.

REM Keep command prompt open
cmd /k
