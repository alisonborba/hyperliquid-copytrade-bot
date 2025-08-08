#!/bin/bash

# Start script for CopyTrade bot
# This script sets up the environment and starts the bot

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

print_header "Starting CopyTrade Bot for Hyperliquid"

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found, creating from example..."
    if [[ -f "env.example" ]]; then
        cp env.example .env
        print_status "Created .env file from example. Please edit it with your configuration."
        print_error "Please configure your .env file before running the bot again."
        exit 1
    else
        print_error "env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.9"

if [[ $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc -l) -eq 0 ]]; then
    print_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

print_status "Python version: $PYTHON_VERSION"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install it first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

print_status "Poetry version: $(poetry --version)"

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    print_status "Creating virtual environment..."
    poetry install
else
    print_status "Virtual environment found, installing dependencies..."
    poetry install
fi

# Check if Redis is running
print_status "Checking Redis connection..."
if ! poetry run python -c "
import redis
import sys
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('Redis is running')
except:
    print('Redis is not running or not accessible')
    sys.exit(1)
" 2>/dev/null; then
    print_warning "Redis is not running. Starting Redis..."
    
    # Try to start Redis with different methods
    if command -v redis-server &> /dev/null; then
        # Start Redis in background
        redis-server --daemonize yes 2>/dev/null || true
        sleep 2
        
        # Check again
        if poetry run python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('Redis started successfully')
except:
    print('Failed to start Redis')
    exit(1)
" 2>/dev/null; then
            print_status "Redis started successfully"
        else
            print_error "Failed to start Redis. Please start it manually:"
            echo "  brew services start redis  # macOS"
            echo "  sudo systemctl start redis  # Linux"
            exit 1
        fi
    else
        print_error "Redis is not installed. Please install it:"
        echo "  brew install redis  # macOS"
        echo "  sudo apt-get install redis-server  # Ubuntu/Debian"
        exit 1
    fi
fi

# Check if node is running
print_status "Checking Hyperliquid node..."
if ! curl -s http://localhost:3001/info -X POST -H "Content-Type: application/json" -d '{"type": "exchangeStatus"}' > /dev/null 2>&1; then
    print_warning "Hyperliquid node is not running or not accessible"
    print_status "You can start it with:"
    echo "  sudo systemctl start hyperliquid-node.service"
    echo "  # or manually: ~/hl/start_node.sh"
    echo ""
    print_warning "The bot will fall back to public API if node is not available"
else
    print_status "Hyperliquid node is running"
fi

# Check environment variables
print_status "Checking environment configuration..."
if ! poetry run python -c "
from copy_trade_bot.config import Config
try:
    config = Config()
    print('Configuration loaded successfully')
    print(f'Chain: {config.hyperliquid_chain}')
    print(f'Node URL: {config.node_info_url}')
    print(f'Database: {config.database_url}')
    print(f'Redis: {config.redis_url}')
except Exception as e:
    print(f'Configuration error: {e}')
    exit(1)
" 2>/dev/null; then
    print_error "Configuration error. Please check your .env file."
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start the bot
print_header "Starting CopyTrade Bot..."
echo ""

# Set environment variables for better logging
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Run the bot with poetry
poetry run python -m copy_trade_bot.main "$@"
