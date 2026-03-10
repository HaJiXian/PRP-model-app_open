@echo off
echo ====================================
echo Psychological Resilience Assessment - Startup Script
echo ====================================
echo.

echo [1/2] Activating virtual environment...
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to create the virtual environment.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated successfully.
echo.

echo [2/2] Starting Flask application...
echo Please make sure LM Studio Server is running!
echo Open browser: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server.
echo.
python app.py

REM If Python exits with error, pause to show error message
if errorlevel 1 (
    echo.
    echo ====================================
    echo Flask application failed to start! Check the error message above.
    echo ====================================
    pause
)
