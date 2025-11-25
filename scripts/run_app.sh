#!/bin/bash

echo "========================================"
echo "  Invoice Generation App Launcher"
echo "========================================"
echo

# Change to the script's directory
cd "$(dirname "$0")"

echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    echo "Please make sure the venv folder exists"
    read -p "Press Enter to continue..."
    exit 1
fi

echo "✅ Virtual environment activated"
echo

echo "Starting Streamlit application..."
echo "Access the app at: http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo

streamlit run app.py

echo
echo "Application stopped."
read -p "Press Enter to continue..."