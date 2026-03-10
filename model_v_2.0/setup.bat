@echo off
echo ====================================
echo Psychological Resilience Assessment - Environment Setup
echo ====================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Failed! Trying with py command...
    py -m venv venv
)
echo Virtual environment created successfully!
echo.

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo [3/4] Installing dependencies...
pip install flask pandas numpy joblib scikit-learn scikit-learn-intelex openai
echo.

echo [4/4] Verifying installation...
pip list
echo.

echo ====================================
echo Setup complete!
echo ====================================
echo.
echo To run the application:
echo   1. cd Desktop/test_cur_app
echo   2. venv\Scripts\activate
echo   3. python app.py
echo.
pause
