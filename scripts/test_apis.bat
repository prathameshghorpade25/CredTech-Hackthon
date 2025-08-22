@echo off
echo ===== CredTech XScore API Testing Utility =====
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not available. Please install Python and try again.
    exit /b 1
)

REM Set the project root directory
set PROJECT_ROOT=%~dp0..

REM Check if .env file exists
if not exist "%PROJECT_ROOT%\.env" (
    echo Warning: .env file not found. Creating from .env.example...
    if exist "%PROJECT_ROOT%\.env.example" (
        copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
        echo Created .env file from .env.example. Please edit it to add your API keys.
    ) else (
        echo Error: .env.example file not found. Please create a .env file manually.
        exit /b 1
    )
)

echo.
echo Choose an option:
echo 1. Quick API Status Check
echo 2. Detailed API Connection Test
echo 3. Test Specific API
echo 4. Exit
echo.

set /p OPTION=Enter option (1-4): 

if "%OPTION%"=="1" (
    echo.
    echo Running quick API status check...
    python "%PROJECT_ROOT%\scripts\check_api_status.py"
) else if "%OPTION%"=="2" (
    echo.
    echo Running detailed API connection test...
    python "%PROJECT_ROOT%\scripts\test_api_connections.py"
) else if "%OPTION%"=="3" (
    echo.
    echo Available APIs:
    echo 1. Alpha Vantage
    echo 2. Financial Modeling Prep
    echo 3. Marketstack
    echo 4. News API
    echo.
    set /p API_OPTION=Enter API to test (1-4): 
    
    if "%API_OPTION%"=="1" (
        python "%PROJECT_ROOT%\scripts\test_api_connections.py" --api alpha_vantage
    ) else if "%API_OPTION%"=="2" (
        python "%PROJECT_ROOT%\scripts\test_api_connections.py" --api financial_modeling_prep
    ) else if "%API_OPTION%"=="3" (
        python "%PROJECT_ROOT%\scripts\test_api_connections.py" --api marketstack
    ) else if "%API_OPTION%"=="4" (
        python "%PROJECT_ROOT%\scripts\test_api_connections.py" --api news_api
    ) else (
        echo Invalid option selected.
    )
) else if "%OPTION%"=="4" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid option selected.
)

echo.
echo For more information on API configuration and troubleshooting,
echo see the API Integration Guide: %PROJECT_ROOT%\docs\api_integration_guide.md

pause