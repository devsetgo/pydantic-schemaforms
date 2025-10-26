#!/bin/bash

# Pydantic Forms Flask Examples Launcher
# This script sets up the environment and runs the Flask demo

echo "🚀 Starting Pydantic Forms Flask Demo"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the pydantic-forms root directory"
    exit 1
fi

# Install the package in development mode
echo "📦 Installing pydantic-forms in development mode..."
pip install -e . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Package installed successfully"
else
    echo "❌ Failed to install package"
    exit 1
fi

# Set PYTHONPATH and run the Flask app
echo "🌐 Starting Flask development server..."
echo "📱 Visit http://localhost:5001 to see the examples"
echo "🔧 Press Ctrl+C to stop the server"
echo "================================================"

export PYTHONPATH=$(pwd)
python examples/flask_examples.py