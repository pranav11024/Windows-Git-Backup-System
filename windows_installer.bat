@echo off
:: Git Backup System - Windows Installer
:: Robust installation and setup script

title Git Backup System Installer
color 0A

echo ================================
echo Git Backup System Installer
echo Windows Edition v1.0
echo ================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator
    echo Some features may require elevated privileges
    echo.
)

:: Check Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

:: Check pip
echo [2/8] Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found
    echo Installing pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pip
        pause
        exit /b 1
    )
)
echo [OK] pip available

:: Check Git installation
echo [3/8] Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found
    echo Please install Git for Windows from:
    echo https://git-scm.com/download/win
    echo Make sure to select "Git Bash Here" option
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('git --version 2^>^&1') do set GIT_VERSION=%%i
echo [OK] Git %GIT_VERSION% found

:: Check Git Bash
echo [4/8] Checking Git Bash...
set GIT_BASH_FOUND=0
if exist "C:\Program Files\Git\bin\bash.exe" (
    set "GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe"
    set GIT_BASH_FOUND=1
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    set "GIT_BASH_PATH=C:\Program Files (x86)\Git\bin\bash.exe"
    set GIT_BASH_FOUND=1
)

if %GIT_BASH_FOUND% == 0 (
    echo [ERROR] Git Bash not found
    echo Please reinstall Git for Windows with Git Bash
    pause
    exit /b 1
)
echo [OK] Git Bash found at "%GIT_BASH_PATH%"

:: Install Python dependencies
echo [5/8] Installing Python dependencies...
echo Installing watchdog...
python -m pip install watchdog>=3.0.0 --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install watchdog
    pause
    exit /b 1
)

echo Installing psutil...
python -m pip install psutil>=5.9.0 --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install psutil
    pause
    exit /b 1
)

echo Installing pywin32...
python -m pip install pywin32>=305 --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pywin32
    pause
    exit /b 1
)
echo [OK] All dependencies installed

:: Create projects directory
echo [6/8] Setting up directories...
set PROJECTS_DIR=%USERPROFILE%\Desktop\projects
if not exist "%PROJECTS_DIR%" (
    mkdir "%PROJECTS_DIR%"
    echo [OK] Created projects directory: %PROJECTS_DIR%
) else (
    echo [OK] Projects directory already exists
)

:: Create sample project
if not exist "%PROJECTS_DIR%\sample_project" (
    mkdir "%PROJECTS_DIR%\sample_project"
    echo # Sample Project > "%PROJECTS_DIR%\sample_project\README.md"
    echo This is a sample project for testing Git backup. >> "%PROJECTS_DIR%\sample_project\README.md"
    echo [OK] Created sample project
)

:: Create configuration file
echo [7/8] Creating configuration...
set CONFIG_FILE=%USERPROFILE%\Desktop\.git_backup_config.json
if not exist "%CONFIG_FILE%" (
    echo { > "%CONFIG_FILE%"
    echo   "backup_interval": 300, >> "%CONFIG_FILE%"
    echo   "auto_push": true, >> "%CONFIG_FILE%"
    echo   "max_file_size_mb": 100, >> "%CONFIG_FILE%"
    echo   "excluded_extensions": [".exe", ".dll", ".bin", ".iso"], >> "%CONFIG_FILE%"
    echo   "projects_path": "%PROJECTS_DIR:\=\\%" >> "%CONFIG_FILE%"
    echo } >> "%CONFIG_FILE%"
    echo [OK] Created default configuration
) else (
    echo [OK] Configuration file already exists
)

:: Create batch files for easy access
echo [8/8] Creating launcher scripts...

:: Start script
echo @echo off > start_backup.bat
echo title Git Backup System >> start_backup.bat
echo cd /d "%~dp0" >> start_backup.bat
echo echo Starting Git Backup System... >> start_backup.bat
echo python git_backup.py start >> start_backup.bat
echo pause >> start_backup.bat

:: Status script
echo @echo off > check_status.bat
echo title Git Backup Status >> check_status.bat
echo cd /d "%~dp0" >> check_status.bat
echo python git_backup.py status >> check_status.bat
echo pause >> check_status.bat

:: GUI script
echo @echo off > config_gui.bat
echo title Git Backup Configuration >> config_gui.bat
echo cd /d "%~dp0" >> config_gui.bat
echo python service_manager.py gui >> config_gui.bat
echo pause >> config_gui.bat

:: Force backup script
echo @echo off > backup_now.bat
echo title Force Backup All Projects >> backup_now.bat
echo cd /d "%~dp0" >> backup_now.bat
echo echo Backing up all projects... >> backup_now.bat
echo python git_backup.py backup-all >> backup_now.bat
echo pause >> backup_now.bat

echo [OK] Created launcher scripts

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo Quick Start:
echo   1. Double-click 'start_backup.bat' to start monitoring
echo   2. Double-click 'config_gui.bat' for GUI configuration
echo   3. Double-click 'check_status.bat' to see repository status
echo   4. Double-click 'backup_now.bat' to force backup all projects
echo.
echo Your projects should be placed in:
echo   %PROJECTS_DIR%
echo.
echo Each folder inside 'projects' becomes a separate Git repository.
echo.
echo Advanced Usage:
echo   python git_backup.py start [interval]  - Start with custom interval
echo   python git_backup.py remote ^<name^> ^<url^> - Add remote repository
echo   python service_manager.py gui         - Open configuration GUI
echo.

:: Offer to create desktop shortcuts
choice /C YN /M "Create desktop shortcuts for easy access?"
if %errorlevel% == 1 (
    echo Creating desktop shortcuts...
    
    :: Create VBS script to make proper shortcuts
    echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcuts.vbs
    echo sLinkFile = "%USERPROFILE%\Desktop\Git Backup - Start.lnk" >> create_shortcuts.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
    echo oLink.TargetPath = "%CD%\start_backup.bat" >> create_shortcuts.vbs
    echo oLink.WorkingDirectory = "%CD%" >> create_shortcuts.vbs
    echo oLink.Description = "Start Git Backup Monitoring" >> create_shortcuts.vbs
    echo oLink.Save >> create_shortcuts.vbs
    
    echo sLinkFile = "%USERPROFILE%\Desktop\Git Backup - Config.lnk" >> create_shortcuts.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcuts.vbs
    echo oLink.TargetPath = "%CD%\config_gui.bat" >> create_shortcuts.vbs
    echo oLink.WorkingDirectory = "%CD%" >> create_shortcuts.vbs
    echo oLink.Description = "Git Backup Configuration" >> create_shortcuts.vbs
    echo oLink.Save >> create_shortcuts.vbs
    
    cscript //nologo create_shortcuts.vbs
    del create_shortcuts.vbs
    echo [OK] Desktop shortcuts created
)

:: Offer to add to startup
choice /C YN /M "Add Git Backup to Windows startup?"
if %errorlevel% == 1 (
    echo Adding to startup...
    set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
    echo @echo off > "%STARTUP_DIR%\GitBackup.bat"
    echo cd /d "%CD%" >> "%STARTUP_DIR%\GitBackup.bat"
    echo start /min python git_backup.py start >> "%STARTUP_DIR%\GitBackup.bat"
    echo [OK] Added to startup - will start automatically when Windows boots
)

echo.
echo Installation completed successfully!
echo Press any key to exit...
pause >nul