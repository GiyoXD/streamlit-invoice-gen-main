@ech  off
REM Universal Invoice Generation App Launcher (Batch Version)
REM This script runs the Invoice app using local Python packages
REM Works on any PC that has run Install_Local_Requirements.ps1

echo =========================================
echo   Universal Invoice App Launcher
echo =========================================
echo.

REM Set code page to UTF-8 to handle Chinese characters
chcp 65001 >nul 2>&1

echo This launcher uses your local Python installation with packages.
echo Make sure you've run Install_Local_Requirements.ps1 first.
echo.

REM Find the shared directory
set "APP_DIR="
echo 🔍 Finding shared directory...

REM Check network paths first
if exist "\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB\app.py" (
    echo ✅ Found application on network share (UNC)
    set "APP_DIR=\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
    goto :FOUND_APP
)

if exist "Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB\app.py" (
    echo ✅ Found application on Z: drive
    set "APP_DIR=Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
    goto :FOUND_APP
)

REM Check script location
if exist "%~dp0app.py" (
    echo ✅ Found application in script directory
    set "APP_DIR=%~dp0"
    REM Remove trailing backslash
    if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"
    goto :FOUND_APP
)

REM Check parent directory
for %%I in ("%~dp0..") do set "PARENT_DIR=%%~fI"
if "%PARENT_DIR:~-1%"=="\" set "PARENT_DIR=%PARENT_DIR:~0,-1%"

if exist "%PARENT_DIR%\app.py" (
    echo ✅ Found application in parent directory
    set "APP_DIR=%PARENT_DIR%"
    goto :FOUND_APP
)

REM If still not found, show error
echo ❌ Could not find the Invoice Generation application.
echo.
echo Please ensure:
echo   1. You have access to the shared folder
echo   2. Or run this script from the application directory
echo.
pause
exit /b 1

:FOUND_APP
echo 📂 Application directory: %APP_DIR%
echo.

REM Try to map network drive if using UNC path
echo %APP_DIR% | findstr /C:"\\" >nul
if %errorlevel% equ 0 (
    echo 🌐 UNC path detected, attempting drive mapping...

    REM Check if Z: is already mapped to the correct location
    net use Z: | findstr /C:"\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Z: drive already mapped to correct location
        set "APP_DIR=Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
    ) else (
        REM Try to map Z: drive if not already mapped correctly
        if not exist "Z:\" (
            echo Mapping Z: drive...
            net use Z: "\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB" /persistent:no >nul 2>&1
            if %errorlevel% equ 0 (
                echo ✅ Drive mapped successfully: Z:
                set "APP_DIR=Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
            ) else (
                echo ⚠️  Drive mapping failed, using UNC path
            )
        ) else (
            echo ⚠️  Z: drive exists but may not be mapped correctly
            echo Checking Z: drive mapping...

            REM Check what Z: is currently mapped to
            net use Z: | findstr /C:"\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB" >nul 2>&1
            if %errorlevel% neq 0 (
                echo 🔄 Z: drive mapped to different location, remapping...
                net use Z: /delete /y >nul 2>&1
                net use Z: "\\Glfnas005\shared\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB" /persistent:no >nul 2>&1
                if %errorlevel% equ 0 (
                    echo ✅ Drive remapped successfully: Z:
                    set "APP_DIR=Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
                ) else (
                    echo ❌ Drive remapping failed, using UNC path
                )
            ) else (
                echo ✅ Z: drive correctly mapped
                set "APP_DIR=Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
            )
        )
    )
    echo.
)

REM Change to application directory
cd /d "%APP_DIR%"
if %errorlevel% neq 0 (
    echo ❌ Failed to change to application directory: %APP_DIR%
    pause
    exit /b 1
)

echo 📂 Changed to application directory: %CD%
echo.

REM Find Python executable
echo 🔍 Finding Python executable...
set "PYTHON_CMD="

REM Try different Python commands
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python -c "import streamlit" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Python found: python
        set "PYTHON_CMD=python"
        goto :PYTHON_FOUND
    )
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    python3 -c "import streamlit" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Python found: python3
        set "PYTHON_CMD=python3"
        goto :PYTHON_FOUND
    )
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    py -c "import streamlit" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Python found: py
        set "PYTHON_CMD=py"
        goto :PYTHON_FOUND
    )
)

REM If no Python with streamlit found
echo ❌ Python not found or streamlit not installed.
echo.
echo Please:
echo   1. Install Python 3.8+ from https://python.org
echo   2. Run: .\Install_Local_Requirements.ps1
echo   3. Make sure Python is in your PATH
echo.
pause
exit /b 1

:PYTHON_FOUND
echo.

REM Check required packages
echo 🔍 Checking required packages...
set "MISSING_PACKAGES="

%PYTHON_CMD% -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 set "MISSING_PACKAGES=%MISSING_PACKAGES% streamlit"

%PYTHON_CMD% -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 set "MISSING_PACKAGES=%MISSING_PACKAGES% pandas"

%PYTHON_CMD% -c "import openpyxl" >nul 2>&1
if %errorlevel% neq 0 set "MISSING_PACKAGES=%MISSING_PACKAGES% openpyxl"

%PYTHON_CMD% -c "import plotly" >nul 2>&1
if %errorlevel% neq 0 set "MISSING_PACKAGES=%MISSING_PACKAGES% plotly"

if defined MISSING_PACKAGES (
    echo ❌ Missing required packages:%MISSING_PACKAGES%
    echo.
    echo Please run: .\Install_Local_Requirements.ps1
    echo.
    pause
    exit /b 1
)

echo ✅ All required packages found
echo.

REM Check if app.py exists
if not exist "app.py" (
    echo ❌ app.py not found in application directory
    pause
    exit /b 1
)

echo ✅ Application files found
echo.

REM Start the application
echo 🚀 Starting Invoice Generation Application...
echo =========================================
echo Application will be available at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo =========================================
echo.

echo 🔧 Starting Streamlit with command:
echo   %PYTHON_CMD% -u -m streamlit run "%APP_DIR%\app.py" --server.headless true --server.runOnSave false --logger.level info
echo.

REM Use -u flag for unbuffered output and additional parameters to prevent hanging
%PYTHON_CMD% -u -m streamlit run "%APP_DIR%\app.py" --server.headless true --server.runOnSave false --logger.level info

echo.
echo 🛑 Application stopped.

REM Clean up network drive if we mapped it
if "%APP_DIR%" neq "Z:\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB" (
    if exist "Z:\" (
        echo 🧹 Cleaning up network drive mapping...
        net use Z: /delete /y >nul 2>&1
        echo ✅ Network drive unmapped
    )
)

echo.
pause