@echo off
REM ========================================
REM GenDesign - Setup Script for Windows 11
REM ========================================
REM This script creates a virtual environment and installs all dependencies

echo.
echo ==========================================
echo  GenDesign AI Beam Design Assistant
echo  Setup Script for Windows 11
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/5] Python found - checking version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo        Python version: %PYTHON_VERSION%

echo.
echo [2/5] Creating virtual environment (.venv)...
if exist ".venv" (
    echo        Virtual environment already exists - removing old one...
    rmdir /s /q ".venv"
)

python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure you have sufficient permissions
    pause
    exit /b 1
)
echo        Virtual environment created successfully

echo.
echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo        Virtual environment activated

echo.
echo [4/5] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)

echo.
echo [5/5] Installing dependencies from requirements.txt...
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found in current directory
    echo Make sure you're running this script from the GenDesign project folder
    pause
    exit /b 1
)

echo        Installing core dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo.
    echo Common solutions:
    echo 1. Make sure you have Microsoft Visual C++ Build Tools installed
    echo 2. Try running as Administrator
    echo 3. Check your internet connection
    echo.
    pause
    exit /b 1
)

echo.
echo [6/6] Testing installation...
python test_dependencies.py
if errorlevel 1 (
    echo WARNING: Some dependencies may not be working correctly
    echo The application might still work, but with limited functionality
)

echo.
echo ==========================================
echo  Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Create a .env file with your Anthropic API key (optional)
echo 2. Run the application using: run.bat
echo.
echo Example .env file content:
echo   ANTHROPIC_API_KEY=your_api_key_here
echo   SECRET_KEY=your_secret_key_here
echo   FLASK_ENV=development
echo   USE_AI_INFERENCE=true
echo.
echo The application will work without API key (physics-only mode)
echo.
pause