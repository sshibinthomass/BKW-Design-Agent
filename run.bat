@echo off
REM ========================================
REM GenDesign - Run Script for Windows 11
REM ========================================
REM This script activates the virtual environment, starts the Flask server, and opens the browser

echo.
echo ==========================================
echo  GenDesign AI Beam Design Assistant
echo  Starting Application...
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first to create the environment
    echo.
    pause
    exit /b 1
)

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo Make sure you're running this script from the GenDesign project folder
    echo.
    pause
    exit /b 1
)

echo [1/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Try running setup.bat again
    pause
    exit /b 1
)
echo        Virtual environment activated

echo.
echo [2/4] Checking Flask installation...
python -c "import flask; print(f'Flask version: {flask.__version__}')" 2>nul
if errorlevel 1 (
    echo ERROR: Flask not found in virtual environment
    echo Try running setup.bat again to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Testing application imports...
echo        Checking if all dependencies load correctly...
python -c "import scipy.optimize; import pandas; import numpy; import plotly; print('All imports successful')" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to import required packages
    echo This might be due to incomplete installation
    echo Try running setup.bat again
    pause
    exit /b 1
)
echo        Dependencies verified successfully

echo.
echo [4/4] Starting Flask server and opening browser...
echo        Server URL: http://localhost:5000
echo        Opening browser in 3 seconds...
echo.

REM Open browser after a short delay
start /b timeout /t 3 /nobreak >nul ^& start http://localhost:5000

echo ==========================================
echo  GenDesign is now running!
echo ==========================================
echo.
echo  Web Interface: http://localhost:5000
echo  AI Features: Available (if API key configured)
echo  Physics Engine: Available
echo  Optimization: Available
echo.
echo Instructions:
echo  - Chat with the AI in English or German
echo  - Upload JSON files with beam specifications
echo  - Ask for beam analysis and optimization
echo  - View interactive 3D visualizations
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python app.py