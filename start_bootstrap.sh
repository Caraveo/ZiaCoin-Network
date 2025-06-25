#!/bin/bash

# ZiaCoin Network Bootstrap Node Startup Script
# This script starts the first node in the network

echo "Starting ZiaCoin Network Bootstrap Node..."
echo "Node IP: 216.255.208.105"
echo "Port: 9999"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import flask, cryptography, requests, aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p wallets/
mkdir -p chain/
mkdir -p logs/

# Set environment variables
export ZIACOIN_NODE_HOST="216.255.208.105"
export ZIACOIN_NODE_PORT="9999"
export ZIACOIN_BOOTSTRAP="true"

# Start the node
echo "Starting bootstrap node..."
echo "Binding to: 0.0.0.0:9999 (all interfaces)"
echo "External access: http://216.255.208.105:9999"
echo "API Status: http://216.255.208.105:9999/status"
echo ""

python3 node.py --port 9999 --host 0.0.0.0 --bootstrap 