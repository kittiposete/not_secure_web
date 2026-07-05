@echo off
echo ==============================================
echo   Starting OWASP ZAP Security Lab Server...
echo ==============================================

:: Check if a virtual environment exists in the standard Windows location
IF EXIST .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) ELSE IF EXIST venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo No virtual environment found. Running with global Python.
)

:: Run the Flask application
echo Starting Flask on http://127.0.0.1:5000...
python app.py

:: Keep the command prompt open if the server crashes
pause
