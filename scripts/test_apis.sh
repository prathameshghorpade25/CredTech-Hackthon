#!/bin/bash

echo "===== CredTech XScore API Testing Utility ====="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not available. Please install Python and try again."
    exit 1
fi

# Determine which Python command to use
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Set the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "Created .env file from .env.example. Please edit it to add your API keys."
    else
        echo "Error: .env.example file not found. Please create a .env file manually."
        exit 1
    fi
fi

echo ""
echo "Choose an option:"
echo "1. Quick API Status Check"
echo "2. Detailed API Connection Test"
echo "3. Test Specific API"
echo "4. Exit"
echo ""

read -p "Enter option (1-4): " OPTION

if [ "$OPTION" = "1" ]; then
    echo ""
    echo "Running quick API status check..."
    $PYTHON_CMD "$PROJECT_ROOT/scripts/check_api_status.py"
elif [ "$OPTION" = "2" ]; then
    echo ""
    echo "Running detailed API connection test..."
    $PYTHON_CMD "$PROJECT_ROOT/scripts/test_api_connections.py"
elif [ "$OPTION" = "3" ]; then
    echo ""
    echo "Available APIs:"
    echo "1. Alpha Vantage"
    echo "2. Financial Modeling Prep"
    echo "3. Marketstack"
    echo "4. News API"
    echo ""
    read -p "Enter API to test (1-4): " API_OPTION
    
    if [ "$API_OPTION" = "1" ]; then
        $PYTHON_CMD "$PROJECT_ROOT/scripts/test_api_connections.py" --api alpha_vantage
    elif [ "$API_OPTION" = "2" ]; then
        $PYTHON_CMD "$PROJECT_ROOT/scripts/test_api_connections.py" --api financial_modeling_prep
    elif [ "$API_OPTION" = "3" ]; then
        $PYTHON_CMD "$PROJECT_ROOT/scripts/test_api_connections.py" --api marketstack
    elif [ "$API_OPTION" = "4" ]; then
        $PYTHON_CMD "$PROJECT_ROOT/scripts/test_api_connections.py" --api news_api
    else
        echo "Invalid option selected."
    fi
elif [ "$OPTION" = "4" ]; then
    echo "Exiting..."
    exit 0
else
    echo "Invalid option selected."
fi

echo ""
echo "For more information on API configuration and troubleshooting,"
echo "see the API Integration Guide: $PROJECT_ROOT/docs/api_integration_guide.md"

read -p "Press Enter to continue..."