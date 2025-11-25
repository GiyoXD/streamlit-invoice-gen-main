@echo off
echo ========================================
echo   Invoice Generation App Launcher
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated.
echo.

echo Starting Streamlit application...
echo Access the app at: http://localhost:8501
echo Close this window to stop the application
echo.

streamlit run app.py

echo.
echo Application stopped.
pause