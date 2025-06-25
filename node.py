#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import sys
import time
import signal
import threading
import requests
from typing import List, Optional, Dict, Any
from aiohttp import web
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from colorama import init, Fore, Style
from modules.utils.print_utils import print_success, print_error, print_warning, print_info
from datetime import datetime

# Suppress Flask development server warning
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Initialize colorama
init()

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import the sync module
from modules.sync.sync import CodeSync
from modules.network.peer import PeerNetwork
from modules.blockchain.blockchain import Blockchain
from modules.mining.miner import Miner
from modules.wallet.wallet import WalletManager

from modules.network.peer import PeerNetwork
from modules.blockchain.blockchain import Blockchain
from modules.mining.miner import Miner
from modules.wallet.wallet import WalletManager
from modules.sync.sync import CodeSync

# Configure logging with colors
from colorama import init, Fore, Style
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            record.msg = f"{self.COLORS[record.levelname]}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class NodeError(Exception):
    """Base exception for node-related errors."""
    pass

class NodeConnectionError(NodeError):
    """Exception for node connection issues."""
    pass

class NodeValidationError(NodeError):
    """Exception for node validation issues."""
    pass

class Node:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port = config['node']['port']
        self.host = config['node']['host']
        self.peers = config['node']['peers']
        self.mining_difficulty = config['blockchain']['difficulty']
        self.mining_reward = config['blockchain']['mining_reward']
        self.block_time = config['blockchain']['block_time']
        self.wallet_path = config['wallet']['storage_path'] if 'wallet' in config else 'wallets/'
        
        # Initialize components with config
        self.blockchain = Blockchain()
        self.peer_network = PeerNetwork(self.blockchain)
        self.miner = Miner(
            self.blockchain.storage,
            target_block_time=self.block_time,
            difficulty=self.mining_difficulty,
            reward=self.mining_reward
        )
        self.wallet_manager = WalletManager(storage_path="chain/wallets/")
        
        # Initialize HTTP app
        self.app = Flask(__name__)
        self.is_running = False
        self.health_check_thread = None
        self.setup_error_handlers()
        self.setup_routes()
        self.setup_signal_handlers()

    def setup_error_handlers(self):
        """Setup error handlers for the Flask application."""
        @self.app.errorhandler(Exception)
        def handle_error(error):
            """Handle all unhandled exceptions."""
            if isinstance(error, HTTPException):
                response = {
                    "error": error.description,
                    "status_code": error.code
                }
                return jsonify(response), error.code
            
            # Log the error
            logger.error(f"Unhandled error: {str(error)}", exc_info=True)
            
            # Return a generic error response
            response = {
                "error": "Internal server error",
                "status_code": 500
            }
            return jsonify(response), 500

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            print_warning("\nShutting down node gracefully...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def health_check(self):
        """Periodic health check of the node."""
        while self.is_running:
            try:
                # Check blockchain health
                if not self.blockchain.is_chain_valid():
                    print_warning("Blockchain validation failed, attempting recovery...")
                    self.blockchain.recover_chain()

                # Check wallet storage
                if not self.wallet_manager.verify_storage():
                    print_warning("Wallet storage verification failed, attempting recovery...")
                    self.wallet_manager.recover_storage()

                # Check node connections
                self.check_peer_connections()

                time.sleep(self.config['node']['health_check_interval'])
            except Exception as e:
                print_error(f"Health check failed: {e}")
                # Don't exit, just log the error and continue
                logger.error(f"Health check error: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying

    def check_peer_connections(self):
        """Check and maintain peer connections."""
        try:
            for peer in self.peers:
                try:
                    response = requests.get(
                        f"http://{peer}/status",
                        timeout=5
                    )
                    if response.status_code != 200:
                        print_warning(f"Peer {peer} is not responding correctly")
                except requests.exceptions.RequestException:
                    print_warning(f"Lost connection to peer {peer}")
        except Exception as e:
            logger.error(f"Error checking peer connections: {e}")

    def setup_routes(self):
        """Setup API routes with error handling."""
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get node status."""
            try:
                return jsonify({
                    'status': 'running',
                    'block_height': len(self.blockchain.chain),
                    'peers': len(self.peers),
                    'pending_transactions': len(self.blockchain.pending_transactions)
                }), 200
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise NodeError("Failed to get node status")

        @self.app.route('/balance/<address>', methods=['GET'])
        def get_balance(address):
            """Get wallet balance."""
            try:
                balance = self.blockchain.get_balance(address)
                return jsonify({'balance': balance}), 200
            except ValueError as e:
                raise NodeValidationError(str(e))
            except Exception as e:
                logger.error(f"Error getting balance: {e}")
                raise NodeError("Failed to get balance")

        @self.app.route('/transaction', methods=['POST'])
        def new_transaction():
            """Create a new transaction."""
            try:
                data = request.get_json()
                if not self.validate_transaction_data(data):
                    raise NodeValidationError("Invalid transaction data")

                # Create transaction object
                from modules.blockchain.blockchain import Transaction
                transaction = Transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=float(data['amount'])
                )
                
                # Sign the transaction
                transaction.sign(data['private_key'])
                
                # Add transaction to blockchain
                transaction_index = self.blockchain.add_transaction(transaction)

                return jsonify({
                    'message': 'Transaction added to pool',
                    'transaction': transaction.to_dict(),
                    'transaction_index': transaction_index
                }), 201
            except ValueError as e:
                raise NodeValidationError(str(e))
            except Exception as e:
                logger.error(f"Error creating transaction: {e}")
                raise NodeError("Failed to create transaction")

        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            """Get the full blockchain."""
            try:
                return jsonify({
                    'chain': [block.to_dict() for block in self.blockchain.chain],
                    'length': len(self.blockchain.chain)
                }), 200
            except Exception as e:
                logger.error(f"Error getting chain: {e}")
                raise NodeError("Failed to get blockchain")

    def validate_transaction_data(self, data: Dict[str, Any]) -> bool:
        """Validate transaction data."""
        required_fields = ['sender', 'recipient', 'amount', 'private_key']
        return all(field in data for field in required_fields)

    def start(self):
        """Start the node."""
        try:
            # Validate configuration
            self._validate_config()
            
            # Initialize components
            self._initialize_components()
            
            # Start health check
            self.is_running = True
            self.health_check_thread = threading.Thread(target=self.health_check)
            self.health_check_thread.daemon = True
            self.health_check_thread.start()

            # Start the node
            print_success("Node started successfully")
            print_info(f"Listening on {self.host}:{self.port}")
            print_info(f"Blockchain difficulty: {self.mining_difficulty}")
            print_info(f"Mining reward: {self.mining_reward}")
            
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,  # Disable debug mode in production
                threaded=True,  # Enable threading for better performance
                use_reloader=False,  # Disable reloader to prevent duplicate processes
                passthrough_errors=True  # Pass through errors instead of handling them
            )
        except Exception as e:
            print_error(f"Failed to start node: {e}")
            self.stop()
            sys.exit(1)

    def _validate_config(self):
        """Validate the node configuration."""
        required_sections = ['node', 'blockchain', 'security', 'logging']
        for section in required_sections:
            if section not in self.config:
                raise NodeError(f"Missing required configuration section: {section}")
        
        required_node_settings = ['host', 'port', 'peers']
        for setting in required_node_settings:
            if setting not in self.config['node']:
                raise NodeError(f"Missing required node setting: {setting}")
        
        # Validate port number
        if not isinstance(self.config['node']['port'], int) or not (1024 <= self.config['node']['port'] <= 65535):
            raise NodeError("Invalid port number. Must be between 1024 and 65535")
        
        # Validate host
        if not isinstance(self.config['node']['host'], str):
            raise NodeError("Invalid host setting")

    def _initialize_components(self):
        """Initialize node components with error handling."""
        try:
            # Initialize blockchain
            if not self.blockchain.initialize():
                raise NodeError("Failed to initialize blockchain")
            
            # Initialize peer network
            if not self.peer_network.initialize():
                raise NodeError("Failed to initialize peer network")
            
            # Initialize miner
            if not self.miner.initialize():
                raise NodeError("Failed to initialize miner")
            
            # Initialize wallet manager
            if not self.wallet_manager.initialize():
                raise NodeError("Failed to initialize wallet manager")
            
            print_success("All components initialized successfully")
        except Exception as e:
            print_error(f"Failed to initialize components: {e}")
            raise NodeError(f"Component initialization failed: {e}")

    def stop(self):
        """Stop the node gracefully."""
        try:
            print_warning("\nShutting down node...")
            self.is_running = False
            
            # Stop health check thread
            if self.health_check_thread:
                self.health_check_thread.join(timeout=5)
            
            # Stop components
            try:
                self.miner.stop_mining()
            except Exception as e:
                print_error(f"Error stopping miner: {e}")
            
            try:
                self.peer_network.stop()
            except Exception as e:
                print_error(f"Error stopping peer network: {e}")
            
            # Save state
            try:
                self.blockchain.save_state()
            except Exception as e:
                print_error(f"Error saving blockchain state: {e}")
            
            try:
                self.wallet_manager.save_state()
            except Exception as e:
                print_error(f"Error saving wallet state: {e}")
            
            print_success("Node stopped gracefully")
        except Exception as e:
            print_error(f"Error during node shutdown: {e}")
            # Don't re-raise the exception to ensure cleanup continues

def load_config() -> Dict[str, Any]:
    """Load configuration from node.conf file."""
    default_config = {
        "node": {
            "host": "localhost",
            "port": 9999,
            "peers": [],
            "health_check_interval": 60,
            "max_peers": 10,
            "sync_interval": 300,
            "max_connections": 100,
            "connection_timeout": 30,
            "request_timeout": 10,
            "max_request_size": 1048576,
            "rate_limit": {
                "requests_per_minute": 100,
                "burst_size": 20
            }
        },
        "blockchain": {
            "difficulty": 4,
            "mining_reward": 50,
            "block_time": 60,
            "max_block_size": 1048576,
            "max_transactions_per_block": 1000,
            "min_transaction_fee": 0.001,
            "max_transaction_fee": 1.0
        },
        "wallet": {
            "storage_path": "wallets/",
            "encryption": {
                "algorithm": "AES-GCM",
                "key_derivation": "PBKDF2",
                "iterations": 100000
            }
        },
        "security": {
            "max_connections": 100,
            "rate_limit": 100,
            "timeout": 30,
            "max_pending_connections": 50,
            "blacklist_duration": 3600,
            "max_failed_attempts": 5,
            "ssl_enabled": False,
            "allowed_origins": ["*"]
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "node.log",
            "max_size": 10485760,
            "backup_count": 5,
            "console_output": True
        },
        "recovery": {
            "auto_recovery": True,
            "max_recovery_attempts": 3,
            "recovery_interval": 300,
            "backup_interval": 3600,
            "max_backups": 24
        },
        "performance": {
            "thread_pool_size": 10,
            "max_workers": 20,
            "queue_size": 1000,
            "cache_size": 1000,
            "garbage_collection_interval": 3600
        }
    }
    
    try:
        if os.path.exists('node.conf'):
            with open('node.conf', 'r') as f:
                user_config = json.load(f)
                # Merge with defaults, keeping user values where provided
                for section in default_config:
                    if section in user_config:
                        default_config[section].update(user_config[section])
                print_success("Configuration loaded successfully")
        else:
            print_warning("No node.conf found, using default configuration")
            
        return default_config
    except Exception as e:
        print_error(f"Error loading node config: {e}")
        print_warning("Using default configuration")
        return default_config

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='ZiaCoin Node')
        parser.add_argument('--genesis', action='store_true', help='Create genesis block')
        parser.add_argument('--bootstrap', action='store_true', help='Run as bootstrap node')
        parser.add_argument('--port', type=int, help='Port to run the node on')
        parser.add_argument('--host', type=str, help='Host to bind the node to')
        args = parser.parse_args()

        # Load configuration
        config = load_config()
        
        # Override config with command line arguments
        if args.port:
            config['node']['port'] = args.port
        if args.host:
            config['node']['host'] = args.host
        if args.bootstrap:
            # Set as bootstrap node
            config['node']['host'] = args.host or config['node']['host']
            config['node']['port'] = args.port or config['node']['port']
            # Add external IP as first peer for other nodes to connect to
            external_peer = "216.255.208.105:9999"
            if external_peer not in config['node']['peers']:
                config['node']['peers'].insert(0, external_peer)
            print_success(f"Starting as bootstrap node on {config['node']['host']}:{config['node']['port']}")
            print_info(f"External access: http://216.255.208.105:9999")
        
        # Create node instance
        node = Node(config)
        
        # Handle genesis block creation
        if args.genesis:
            try:
                print_info("Creating genesis block...")
                node.blockchain.create_genesis_block()
                print_success("Genesis block created successfully")
                return
            except Exception as e:
                print_error(f"Failed to create genesis block: {e}")
                sys.exit(1)
        
        # Start the node
        node.start()
    except KeyboardInterrupt:
        print_warning("\nNode shutdown initiated by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 