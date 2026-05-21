@echo off
echo ==========================================
echo   CHAFF Ghost Engine - Windows Installer
echo ==========================================
echo.
echo Step 1: Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Download from https://python.org
    pause
    exit /b 1
)
echo.
echo Step 2: Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Step 3: Checking for Ollama...
ollama --version
if errorlevel 1 (
    echo.
    echo Ollama not found. For best content quality, install it:
    echo   1. Go to https://ollama.com
    echo   2. Download and install Ollama for Windows
    echo   3. Open a new terminal and run: ollama pull mistral
    echo.
    echo The ghost engine will still work without Ollama
    echo using template-based content generation.
) else (
    echo Ollama found! Pulling mistral model...
    ollama pull mistral
)
echo.
echo ==========================================
echo   Installation complete!
echo   Run run_dry.bat to test your setup.
echo ==========================================
pause
