#!/bin/bash
#
# FastAPI Pydantic Forms Demo Installation & Run Script
# ====================================================
#
# This script installs dependencies and runs the FastAPI demo.
#
# Usage:
#     ./run_fastapi_demo.sh          # Install deps and run server
#     ./run_fastapi_demo.sh --dev    # Run in development mode with reload
#     ./run_fastapi_demo.sh --help   # Show this help
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLES_DIR="$PROJECT_ROOT/examples"

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}FastAPI Pydantic Forms Demo${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_help() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    --dev       Run in development mode with auto-reload
    --port PORT Set custom port (default: 8000)
    --host HOST Set custom host (default: 0.0.0.0)
    --help      Show this help message

EXAMPLES:
    $0                          # Basic run
    $0 --dev                    # Development mode
    $0 --port 8080              # Custom port
    $0 --host localhost --dev   # Local dev mode

ENVIRONMENT SUPPORT:
    • Devcontainer/Codespaces: Automatically detected, no venv needed
    • Local development: Uses virtual environment if available
    • Docker: Automatically detected, works without venv

The FastAPI demo showcases:
    • Async form rendering for high performance
    • Bootstrap 5 and Material Design 3 themes  
    • Multiple layouts: vertical, horizontal, side-by-side, tabbed
    • Complete form validation and error handling
    • Modern Python 3.14+ template strings
    • FastAPI async route handlers
EOF
}

check_python() {
    echo -e "${YELLOW}Checking Python version...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 not found. Please install Python 3.11+${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
    
    # Check if version is at least 3.11
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo -e "${RED}Warning: Python 3.11+ recommended for best compatibility${NC}"
        echo -e "${YELLOW}Current version: $PYTHON_VERSION${NC}"
    fi
}

install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if we're in a devcontainer (no need for venv)
    if [ -n "$DEVCONTAINER" ] || [ -n "$CODESPACES" ] || [ -f "/.dockerenv" ]; then
        echo -e "${GREEN}✓ Running in devcontainer - skipping virtual environment setup${NC}"
        
        # Upgrade pip
        pip install --upgrade pip > /dev/null 2>&1
        
        # Install requirements
        echo -e "${YELLOW}Installing project requirements...${NC}"
        pip install -r requirements.txt > /dev/null 2>&1
        
        # Install the package in development mode
        echo -e "${YELLOW}Installing pydantic-forms in development mode...${NC}"
        pip install -e . > /dev/null 2>&1
    else
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            echo -e "${YELLOW}Creating virtual environment...${NC}"
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Upgrade pip
        pip install --upgrade pip > /dev/null 2>&1
        
        # Install requirements
        echo -e "${YELLOW}Installing project requirements...${NC}"
        pip install -r requirements.txt > /dev/null 2>&1
        
        # Install the package in development mode
        echo -e "${YELLOW}Installing pydantic-forms in development mode...${NC}"
        pip install -e . > /dev/null 2>&1
    fi
    
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
}

run_server() {
    local dev_mode=$1
    local host=${2:-"0.0.0.0"}
    local port=${3:-8000}
    
    cd "$EXAMPLES_DIR"
    
    # Activate virtual environment only if not in devcontainer
    if [ ! -n "$DEVCONTAINER" ] && [ ! -n "$CODESPACES" ] && [ ! -f "/.dockerenv" ] && [ -d "$PROJECT_ROOT/venv" ]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
    
    # Check if templates directory exists
    if [ ! -d "templates" ]; then
        echo -e "${RED}Error: templates directory not found in $EXAMPLES_DIR${NC}"
        echo -e "${YELLOW}Make sure you're running the script from the correct directory${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Starting FastAPI server...${NC}"
    echo -e "${BLUE}📄 Home page: http://localhost:$port/${NC}"
    echo -e "${BLUE}🎨 Bootstrap demos: http://localhost:$port/bootstrap/minimal${NC}"
    echo -e "${BLUE}🎨 Material demos: http://localhost:$port/material/minimal${NC}"
    echo -e "${BLUE}📐 Layout demos: http://localhost:$port/layouts${NC}"
    echo -e "${BLUE}⚡ Async rendering with FastAPI${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""
    
    if [ "$dev_mode" = true ]; then
        echo -e "${GREEN}Running in development mode with auto-reload...${NC}"
        uvicorn fastapi_demo:app --host "$host" --port "$port" --reload
    else
        echo -e "${GREEN}Running in production mode...${NC}"
        uvicorn fastapi_demo:app --host "$host" --port "$port"
    fi
}

# Parse command line arguments
DEV_MODE=false
HOST="0.0.0.0"
PORT=8000

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    check_python
    echo ""
    
    install_dependencies
    echo ""
    
    run_server "$DEV_MODE" "$HOST" "$PORT"
}

# Run main function
main