#!/bin/bash
set -e  # Exit on error

# Pydantic Forms Flask Examples Launcher
# This script sets up the environment and runs the Flask demo

echo "🚀 Starting Pydantic Forms Flask Demo"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the pydantic-forms root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Install the package in development mode
echo "📦 Installing pydantic-forms in development mode..."
if pip install -e . > /dev/null 2>&1; then
    echo "✅ Package installed successfully"
else
    echo "❌ Failed to install package"
    exit 1
fi

# Check if Flask example file exists
if [ ! -f "examples/flask_examples.py" ]; then
    echo "❌ Flask examples file not found at examples/flask_examples.py"
    exit 1
fi

# Set PYTHONPATH and run the Flask app
echo "🌐 Starting Flask development server..."
echo "📱 Visit http://localhost:5001 to see the examples"
echo "🔧 Press Ctrl+C to stop the server"
echo "================================================"

export PYTHONPATH=$(pwd)
python3 examples/flask_examples.py
