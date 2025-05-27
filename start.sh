#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[$timestamp] INFO: $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] WARNING: $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR: $message${NC}"
            ;;
    esac
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    log "ERROR" "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "env" ]; then
    log "INFO" "First time setup detected. Creating virtual environment..."
    
    # Create virtual environment
    if ! python3 -m venv env; then
        log "ERROR" "Failed to create virtual environment"
        exit 1
    fi
    log "INFO" "Virtual environment created successfully"
    
    # Activate virtual environment
    log "INFO" "Activating virtual environment..."
    source env/bin/activate || {
        log "ERROR" "Failed to activate virtual environment"
        exit 1
    }
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        log "ERROR" "requirements.txt not found"
        exit 1
    fi
    
    # Install requirements
    log "INFO" "Installing requirements..."
    if ! pip3 install -r requirements.txt; then
        log "ERROR" "Failed to install requirements"
        exit 1
    fi
    log "INFO" "Requirements installed successfully"
    
    # Check if chain.config exists
    if [ ! -f "chain.config" ]; then
        log "WARNING" "chain.config not found. Using default configuration."
    fi
    
    # Mine genesis block
    log "INFO" "Mining genesis block..."
    if ! python3 node.py --genesis; then
        log "ERROR" "Failed to mine genesis block"
        exit 1
    fi
    log "INFO" "Genesis block mined successfully"
    
    log "INFO" "First time setup completed successfully"
else
    # Activate existing virtual environment
    log "INFO" "Activating existing virtual environment..."
    source env/bin/activate || {
        log "ERROR" "Failed to activate virtual environment"
        exit 1
    }
fi

# Start the node
log "INFO" "Starting ZiaCoin node..."
if ! python3 node.py; then
    log "ERROR" "Node failed to start"
    exit 1
fi

# Deactivate virtual environment on exit
deactivate
log "INFO" "Node stopped"
