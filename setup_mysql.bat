@echo off
echo 🚀 MySQL Setup for Job Automation Application
echo ========================================
echo.

REM Check if MySQL is installed
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ MySQL not found. Please install MySQL first.
    echo Download from: https://dev.mysql.com/downloads/mysql/
    pause
    exit /b 1
)

echo ✅ MySQL found and accessible
echo.

REM Get database details
set /p host="MySQL host [localhost]: "
if "%host%"=="" set host=localhost

set /p port="MySQL port [3306]: "
if "%port%"=="" set port=3306

set /p root_user="MySQL root username [root]: "
if "%root_user%"=="" set root_user=root

set /p root_password="MySQL root password: "

echo.
echo Creating database 'job_automation'...
mysql -h %host% -P %port% -u %root_user% -p%root_password% -e "CREATE DATABASE IF NOT EXISTS job_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if %errorlevel% neq 0 (
    echo ❌ Failed to create database
    pause
    exit /b 1
)

echo ✅ Database created successfully
echo.

REM Get application user details
set /p username="Application username [job_user]: "
if "%username%"=="" set username=job_user

set /p password="Application password: "

echo.
echo Creating user '%username%'...
mysql -h %host% -P %port% -u %root_user% -p%root_password% -e "CREATE USER IF NOT EXISTS '%username%'@'localhost' IDENTIFIED BY '%password%'; GRANT ALL PRIVILEGES ON job_automation.* TO '%username%'@'localhost'; FLUSH PRIVILEGES;"
if %errorlevel% neq 0 (
    echo ❌ Failed to create user
    pause
    exit /b 1
)

echo ✅ User created successfully
echo.

echo 🎉 MySQL setup completed successfully!
echo.
echo Next steps:
echo 1. Install MySQL client: pip install mysqlclient
echo 2. Test connection: python test_system.py
echo 3. Initialize database: python cli.py init
echo.
echo Configuration details:
echo - Host: %host%
echo - Port: %port%
echo - Database: job_automation
echo - Username: %username%
echo - Password: %password%
echo.

pause

