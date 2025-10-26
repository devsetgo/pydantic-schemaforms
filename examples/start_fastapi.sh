#!/bin/bash
#
# Quick FastAPI Demo Starter
# ==========================
#
# Simple script to start the FastAPI demo without dependency installation.
# Perfect for devcontainers where dependencies are already installed.
#
# Usage:
#     ./start_fastapi.sh          # Start server on port 8000
#     ./start_fastapi.sh --dev    # Start with auto-reload
#     ./start_fastapi.sh --port 8080  # Custom port
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEV_MODE=false
PORT=8000
HOST="0.0.0.0"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "OPTIONS:"
            echo "    --dev       Run with auto-reload (development mode)"
            echo "    --port PORT Set custom port (default: 8000)"
            echo "    --host HOST Set custom host (default: 0.0.0.0)"
            echo "    --help      Show this help message"
            echo ""
            echo "EXAMPLES:"
            echo "    $0                    # Start on port 8000"
            echo "    $0 --dev             # Development mode with reload"
            echo "    $0 --port 8080       # Custom port"
            echo "    $0 --dev --port 9000 # Dev mode on port 9000"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in the examples directory
if [ ! -f "fastapi_demo.py" ]; then
    echo -e "${YELLOW}Moving to examples directory...${NC}"
    cd "$(dirname "$0")"
fi

# Check if templates directory exists
if [ ! -d "templates" ]; then
    echo "Error: templates directory not found"
    echo "Make sure you're running this script from the examples directory"
    exit 1
fi

echo -e "${GREEN}🚀 Starting FastAPI Pydantic Forms Demo...${NC}"
echo -e "${BLUE}📄 Home page: http://localhost:$PORT/${NC}"
echo -e "${BLUE}🎨 Bootstrap demos: http://localhost:$PORT/bootstrap/minimal${NC}"
echo -e "${BLUE}🎨 Material demos: http://localhost:$PORT/material/minimal${NC}"
echo -e "${BLUE}📐 Layout demos: http://localhost:$PORT/layouts${NC}"
echo -e "${BLUE}⚡ Async rendering with FastAPI${NC}"
echo ""

if [ "$DEV_MODE" = true ]; then
    echo -e "${GREEN}Running in development mode with auto-reload...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""
    uvicorn fastapi_demo:app --host "$HOST" --port "$PORT" --reload
else
    echo -e "${GREEN}Running in production mode...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""
    uvicorn fastapi_demo:app --host "$HOST" --port "$PORT"
fi