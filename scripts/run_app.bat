@echo off
echo ========================================
echo   Invoice Generation App Launcher
echo ========================================
echo.

echo Checking if running from network path...
if "%~d0"=="\\" (
    echo ⚠️  Running from network share detected
    echo Please map the network drive first:
    echo Example: net use Z: "\\Glfnas005\共享文件夹\营销团队\software to use\GENERATE_INVOICE_STREAMLIT_WEB"
    echo Then run: Z:\run_app.bat
    echo.
    pause
    exit /b 1
)

REM Change to the script's directory to ensure correct working directory
cd /d "%~dp0"

echo Activating virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found at: %CD%\venv
    echo Please make sure you're running this from the correct directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    echo Please make sure the venv folder exists and is accessible
    pause
    exit /b 1
)

echo ✅ Virtual environment activated
echo.

echo Starting Streamlit application...
echo Access the app at: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

streamlit run app.py

echo.
echo Application stopped.
pause