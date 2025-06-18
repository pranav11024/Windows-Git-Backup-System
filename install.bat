
@echo off
echo Installing Git Backup System for Windows...
pip install watchdog psutil pywin32
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    echo Make sure Python and pip are installed
    pause
    exit /b 1
)

echo.
echo Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git not found. Please install Git for Windows from:
    echo https://git-scm.com/download/win
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo Usage:
echo   python git_backup.py start       - Start monitoring
echo   python git_backup.py status      - Check repositories
echo   python git_backup.py backup-all  - Force backup all projects
echo.
pause
