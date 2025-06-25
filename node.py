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
from colorama import init, Fore, Style
from modules.utils.print_utils import print_success, print_error, print_warning, print_info
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Suppress Flask development server warning
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Enable Flask logging to see server startup
logging.getLogger('werkzeug').setLevel(logging.INFO)

# Initialize colorama
init()

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import modules
from modules.sync.sync import CodeSync
from modules.network.peer import PeerNetwork
from modules.blockchain.blockchain import Blockchain
from modules.mining.miner import Miner
from modules.wallet.wallet import WalletManager

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
    def __init__(self, config: Dict[str, Any], is_initial_node: bool = False):
        self.config = config
        self.is_initial_node = is_initial_node
        self.host = config['node']['host']
        self.port = config['node']['port']
        self.peers = config['node']['peers']
        self.mining_difficulty = config['blockchain']['difficulty']
        self.mining_reward = config['blockchain']['mining_reward']
        self.block_time = config['blockchain']['block_time']
        self.wallet_path = config['wallet']['storage_path'] if 'wallet' in config else 'wallets/'
        
        # Initialize components with config
        self.blockchain = Blockchain()
        self.peer_network = PeerNetwork(self.blockchain, is_initial_node=self.is_initial_node)
        self.miner = Miner(self.blockchain.storage, target_block_time=self.block_time, difficulty=self.mining_difficulty, reward=self.mining_reward)
        self.wallet_manager = WalletManager(storage_path=self.wallet_path)
        
        # Initialize HTTP app
        self.app = FastAPI()
        self.is_running = False
        self.health_check_thread = None
        self.setup_error_handlers()
        self.setup_routes()
        self.setup_signal_handlers()

    def setup_error_handlers(self):
        @self.app.exception_handler(Exception)
        async def handle_error(request: Request, exc: Exception):
            if isinstance(exc, HTTPException):
                return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "status_code": exc.status_code})
            logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
            return JSONResponse(status_code=500, content={"error": "Internal server error", "status_code": 500})

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            print_warning("\nShutting down node gracefully...")
            self.stop()
            sys.exit(0)

        # Temporarily disable signal handlers to prevent interference with Flask
        # signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGTERM, signal_handler)
        print_info("Signal handlers temporarily disabled for Flask compatibility")

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
                
        print_info("Health check thread stopped")

    def check_peer_connections(self):
        """Check and maintain peer connections."""
        try:
            # Skip peer connection checks for initial nodes
            if self.is_initial_node:
                return
                
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
        """Setup FastAPI routes."""
        app = self.app
        node = self

        @app.get('/')
        async def root():
            """Root endpoint that redirects to status."""
            return {
                'message': 'ZiaCoin Node API',
                'version': '1.0.0',
                'endpoints': {
                    'status': '/status',
                    'peers': '/peers',
                    'network': '/network',
                    'chain': '/chain',
                    'health': '/health',
                    'docs': '/docs'
                },
                'node_type': 'initial' if node.is_initial_node else 'regular',
                'external_access': f"http://216.255.208.105:{node.port}" if node.is_initial_node else None
            }

        @app.get('/status')
        async def get_status():
            try:
                peer_list = node.peer_network.get_peer_list() if hasattr(node.peer_network, 'get_peer_list') else []
                peer_count = len(peer_list)
                return {
                    'status': 'running',
                    'node_type': 'initial' if node.is_initial_node else 'regular',
                    'host': node.host,
                    'port': node.port,
                    'block_height': len(node.blockchain.chain),
                    'peer_count': peer_count,
                    'peers': peer_list,
                    'pending_transactions': len(node.blockchain.pending_transactions),
                    'mining_difficulty': node.mining_difficulty,
                    'mining_reward': node.mining_reward,
                    'is_initial_node': node.is_initial_node,
                    'external_access': f"http://216.255.208.105:{node.port}" if node.is_initial_node else None
                }
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail="Failed to get node status")

        @app.get('/peers')
        async def get_peers():
            try:
                peer_list = node.peer_network.get_peer_list() if hasattr(node.peer_network, 'get_peer_list') else []
                return {
                    'peer_count': len(peer_list),
                    'peers': peer_list,
                    'node_type': 'initial' if node.is_initial_node else 'regular',
                    'host': node.host,
                    'port': node.port
                }
            except Exception as e:
                logger.error(f"Error getting peers: {e}")
                raise HTTPException(status_code=500, detail="Failed to get peer information")

        @app.post('/peers/connect')
        async def connect_peer(request: Request):
            try:
                data = await request.json()
                if not data or 'host' not in data or 'port' not in data:
                    raise HTTPException(status_code=400, detail="Missing host or port in request")
                host = data['host']
                port = int(data['port'])
                success = node.peer_network._connect_to_peer(host, port)
                if success:
                    return {
                        'message': f'Successfully connected to peer {host}:{port}',
                        'peer': f'{host}:{port}',
                        'status': 'connected'
                    }
                else:
                    return JSONResponse(status_code=400, content={
                        'message': f'Failed to connect to peer {host}:{port}',
                        'peer': f'{host}:{port}',
                        'status': 'failed'
                    })
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error connecting to peer: {e}")
                raise HTTPException(status_code=500, detail="Failed to connect to peer")

        @app.get('/network')
        async def get_network_info():
            try:
                peer_list = node.peer_network.get_peer_list() if hasattr(node.peer_network, 'get_peer_list') else []
                active_peers = len([p for p in peer_list if p.get('is_active', True)])
                inactive_peers = len([p for p in peer_list if not p.get('is_active', True)])
                return {
                    'network_status': 'active',
                    'node_type': 'initial' if node.is_initial_node else 'regular',
                    'node_address': f"{node.host}:{node.port}",
                    'total_peers': len(peer_list),
                    'active_peers': active_peers,
                    'inactive_peers': inactive_peers,
                    'peer_details': peer_list,
                    'initial_node': '216.255.208.105:9999',
                    'is_connected_to_initial': any('216.255.208.105:9999' in str(p) for p in peer_list),
                    'blockchain_height': len(node.blockchain.chain),
                    'pending_transactions': len(node.blockchain.pending_transactions)
                }
            except Exception as e:
                logger.error(f"Error getting network info: {e}")
                raise HTTPException(status_code=500, detail="Failed to get network information")

        @app.get('/network/stats')
        async def get_network_stats():
            try:
                stats = node.peer_network.get_network_stats() if hasattr(node.peer_network, 'get_network_stats') else {}
                return {
                    'network_statistics': stats,
                    'node_info': {
                        'type': 'initial' if node.is_initial_node else 'regular',
                        'address': f"{node.host}:{node.port}",
                        'is_initial_node': node.is_initial_node
                    }
                }
            except Exception as e:
                logger.error(f"Error getting network stats: {e}")
                raise HTTPException(status_code=500, detail="Failed to get network statistics")

        @app.get('/balance/{address}')
        async def get_balance(address: str):
            try:
                balance = node.blockchain.get_balance(address)
                return {'balance': balance}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting balance: {e}")
                raise HTTPException(status_code=500, detail="Failed to get balance")

        @app.post('/transaction')
        async def new_transaction(request: Request):
            try:
                data = await request.json()
                if not node.validate_transaction_data(data):
                    raise HTTPException(status_code=400, detail="Invalid transaction data")
                from modules.blockchain.blockchain import Transaction
                transaction = Transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=float(data['amount'])
                )
                transaction.sign(data['private_key'])
                transaction_index = node.blockchain.add_transaction(transaction)
                return {
                    'message': 'Transaction added to pool',
                    'transaction': transaction.to_dict(),
                    'transaction_index': transaction_index
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error creating transaction: {e}")
                raise HTTPException(status_code=500, detail="Failed to create transaction")

        @app.get('/chain')
        async def get_chain():
            try:
                return {
                    'chain': [block.to_dict() for block in node.blockchain.chain],
                    'length': len(node.blockchain.chain)
                }
            except Exception as e:
                logger.error(f"Error getting chain: {e}")
                raise HTTPException(status_code=500, detail="Failed to get blockchain")

        # Add a simple health check endpoint
        @app.get('/health')
        async def health_check():
            return {'status': 'healthy', 'timestamp': time.time()}

    def validate_transaction_data(self, data: Dict[str, Any]) -> bool:
        """Validate transaction data."""
        required_fields = ['sender', 'recipient', 'amount', 'private_key']
        return all(field in data for field in required_fields)

    def start(self):
        try:
            self._validate_config()
            print_info("Initializing components...")
            try:
                self._initialize_components()
                print_success("All components initialized successfully")
            except Exception as e:
                print_warning(f"Some components failed to initialize: {e}")
                print_info("Continuing with node startup...")
            
            self.is_running = True
            
            # Start health check thread
            self.health_check_thread = threading.Thread(target=self.health_check)
            self.health_check_thread.daemon = True
            self.health_check_thread.start()
            print_info("Health check thread started (daemon)")

            print_success("Node started successfully")
            print_info(f"Node listening on {self.host}:{self.port}")
            print_info(f"Blockchain difficulty: {self.mining_difficulty}")
            print_info(f"Mining reward: {self.mining_reward}")
            if hasattr(self.peer_network, 'get_network_stats'):
                stats = self.peer_network.get_network_stats()
                print_info(f"Network Status: {stats.get('connection_rate', '0/0')} peers connected")
                if self.is_initial_node:
                    print_info("🌐 Initial Node Mode - Other nodes will connect to this node")
                else:
                    print_info("🔗 Regular Node Mode - Connected to initial node")
            print_info("💡 Node logic is running. To start API server, run: python node.py --api")
            
            # Keep the main thread alive
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print_warning("\nShutdown signal received...")
                self.stop()
                
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

    def _start_peer_network(self, port, peers, require_initial_node):
        """Start peer network in a separate thread with error handling."""
        try:
            self.peer_network.start(
                port=port,
                bootstrap_nodes=peers,
                require_initial_node=require_initial_node
            )
            print_success("Peer network started successfully")
        except ConnectionError as e:
            if not self.is_initial_node:
                print_warning(f"Failed to connect to initial node: {e}, continuing...")
            else:
                print_warning(f"Initial node mode - skipping initial node validation: {e}")
        except Exception as e:
            print_warning(f"Peer network start error: {e}, continuing...")

    def _initialize_components(self):
        """Initialize node components with error handling."""
        try:
            # Initialize blockchain with timeout
            print_info("Initializing blockchain...")
            try:
                if not self.blockchain.initialize():
                    print_warning("Blockchain initialization failed, continuing...")
                else:
                    print_success("Blockchain initialized successfully")
            except Exception as e:
                print_warning(f"Blockchain initialization error: {e}, continuing...")
            
            # Initialize peer network with timeout
            print_info("Initializing peer network...")
            try:
                if not self.peer_network.initialize():
                    print_warning("Peer network initialization failed, continuing...")
                else:
                    print_success("Peer network initialized successfully")
            except Exception as e:
                print_warning(f"Peer network initialization error: {e}, continuing...")
            
            # Start peer network with initial node validation
            try:
                # Initial nodes don't require connection to themselves
                require_initial_node = not self.is_initial_node
                
                # Start peer network in a separate thread to prevent blocking Flask
                peer_start_thread = threading.Thread(
                    target=self._start_peer_network,
                    args=(self.port, self.peers, require_initial_node)
                )
                peer_start_thread.daemon = True
                peer_start_thread.start()
                
                print_success("Peer network start initiated (non-blocking)")
            except Exception as e:
                print_warning(f"Peer network start error: {e}, continuing...")
            
            # Initialize miner with timeout
            print_info("Initializing miner...")
            try:
                if not self.miner.initialize():
                    print_warning("Miner initialization failed, continuing...")
                else:
                    print_success("Miner initialized successfully")
            except Exception as e:
                print_warning(f"Miner initialization error: {e}, continuing...")
            
            # Initialize wallet manager with timeout
            print_info("Initializing wallet manager...")
            try:
                if not self.wallet_manager.initialize():
                    print_warning("Wallet manager initialization failed, continuing...")
                else:
                    print_success("Wallet manager initialized successfully")
            except Exception as e:
                print_warning(f"Wallet manager initialization error: {e}, continuing...")
            
            print_success("Component initialization completed (some may have failed)")
        except Exception as e:
            print_error(f"Critical error during component initialization: {e}")
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
        parser.add_argument('--init', action='store_true', help='Run as initial bootstrap node (node logic only)')
        parser.add_argument('--bootstrap', action='store_true', help='Run as bootstrap node')
        parser.add_argument('--test', action='store_true', help='Run in test mode - connect to test initial node')
        parser.add_argument('--port', type=int, help='Port to run the node on')
        parser.add_argument('--host', type=str, help='Host to bind the node to')
        parser.add_argument('--api', action='store_true', help='Run only the FastAPI server (no node logic)')
        args = parser.parse_args()

        # Load configuration
        config = load_config()
        if args.port:
            config['node']['port'] = args.port
        if args.host:
            config['node']['host'] = args.host

        # Handle API-only mode
        if args.api:
            # Use a different port for the API frontend
            api_port = args.port or 8000
            print_success(f"🚀 Starting FastAPI server as frontend...")
            print_info(f"API Server: http://{config['node']['host']}:{api_port}")
            print_info("📡 This API server connects to the node backend")
            print_info("📡 Available API Endpoints:")
            print_info("  └─ GET  /                - API root and info")
            print_info("  └─ GET  /status          - Node status and peer count")
            print_info("  └─ GET  /peers           - Connected peers list")
            print_info("  └─ GET  /network         - Detailed network information")
            print_info("  └─ GET  /network/stats   - Network statistics")
            print_info("  └─ GET  /chain           - Full blockchain")
            print_info("  └─ GET  /balance/<addr>  - Wallet balance")
            print_info("  └─ POST /transaction     - Create new transaction")
            print_info("  └─ POST /peers/connect   - Manually connect to peer")
            print_info("  └─ GET  /health          - Health check")
            print_info("  └─ GET  /docs            - API documentation")
            
            # Create a proxy API server that connects to the node
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.responses import JSONResponse
            import requests
            
            app = FastAPI()
            NODE_BACKEND_URL = "http://127.0.0.1:9999"
            
            @app.get('/')
            async def root():
                """Root endpoint that shows API info."""
                return {
                    'message': 'ZiaCoin Node API (Frontend)',
                    'version': '1.0.0',
                    'backend_url': NODE_BACKEND_URL,
                    'frontend_url': f"http://{config['node']['host']}:{api_port}",
                    'endpoints': {
                        'status': '/status',
                        'peers': '/peers',
                        'network': '/network',
                        'chain': '/chain',
                        'health': '/health',
                        'docs': '/docs'
                    },
                    'node_type': 'api_frontend',
                    'note': 'This API server connects to the node backend'
                }
            
            @app.get('/status')
            async def get_status():
                """Proxy status request to node backend."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/status", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        data['api_server'] = 'frontend'
                        data['backend_url'] = NODE_BACKEND_URL
                        return data
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend. Make sure the node is running with: python node.py --init")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.get('/peers')
            async def get_peers():
                """Proxy peers request to node backend."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/peers", timeout=5)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.get('/network')
            async def get_network():
                """Proxy network request to node backend."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/network", timeout=5)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.get('/chain')
            async def get_chain():
                """Proxy chain request to node backend."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/chain", timeout=10)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.get('/balance/{address}')
            async def get_balance(address: str):
                """Proxy balance request to node backend."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/balance/{address}", timeout=5)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.post('/transaction')
            async def new_transaction(request: Request):
                """Proxy transaction request to node backend."""
                try:
                    data = await request.json()
                    response = requests.post(f"{NODE_BACKEND_URL}/transaction", json=data, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Backend node not responding")
                except requests.exceptions.ConnectionError:
                    raise HTTPException(status_code=503, detail="Cannot connect to node backend")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error connecting to backend: {str(e)}")
            
            @app.get('/health')
            async def health_check():
                """Health check that also checks backend connectivity."""
                try:
                    response = requests.get(f"{NODE_BACKEND_URL}/health", timeout=5)
                    if response.status_code == 200:
                        return {
                            'status': 'healthy',
                            'api_server': 'frontend',
                            'backend_connected': True,
                            'backend_url': NODE_BACKEND_URL,
                            'timestamp': time.time()
                        }
                    else:
                        return {
                            'status': 'degraded',
                            'api_server': 'frontend',
                            'backend_connected': False,
                            'backend_url': NODE_BACKEND_URL,
                            'backend_status': response.status_code,
                            'timestamp': time.time()
                        }
                except requests.exceptions.ConnectionError:
                    return {
                        'status': 'unhealthy',
                        'api_server': 'frontend',
                        'backend_connected': False,
                        'backend_url': NODE_BACKEND_URL,
                        'error': 'Cannot connect to backend',
                        'timestamp': time.time()
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'api_server': 'frontend',
                        'backend_connected': False,
                        'backend_url': NODE_BACKEND_URL,
                        'error': str(e),
                        'timestamp': time.time()
                    }
            
            # Run FastAPI server
            uvicorn.run(
                app, 
                host=config['node']['host'], 
                port=api_port, 
                log_level="info",
                access_log=True
            )
            return

        # Handle initial node (216.255.208.105)
        if args.init:
            config['node']['host'] = args.host or "127.0.0.1"  # Bind to localhost
            config['node']['port'] = args.port or 9999
            print_success(f"Starting as INITIAL bootstrap node on {config['node']['host']}:{config['node']['port']}")
            print_info(f"Mainnet access: http://216.255.208.105:9999")
            print_info("This is the main network entry point")
            print_info("Note: External access requires port forwarding to 216.255.208.105:9999")
            print_info("💡 To start API server separately, run: python node.py --api")
        elif args.bootstrap:
            config['node']['host'] = args.host or config['node']['host']
            config['node']['port'] = args.port or config['node']['port']
            external_peer = "216.255.208.105:9999"
            if external_peer not in config['node']['peers']:
                config['node']['peers'].insert(0, external_peer)
            print_success(f"Starting as bootstrap node on {config['node']['host']}:{config['node']['port']}")
            print_info(f"External access: http://216.255.208.105:9999")
        else:
            print_info("Regular node mode - attempting to connect to initial node...")
            if args.test:
                initial_node = "127.0.0.1:9999"
                print_info("🧪 Test mode - connecting to test initial node")
            else:
                initial_node = "216.255.208.105:9999"
                print_info("🌐 Mainnet mode - connecting to mainnet initial node")
            try:
                import requests
                response = requests.get(f"http://{initial_node}/status", timeout=10)
                if response.status_code == 200:
                    print_success(f"✓ Connected to initial node: {initial_node}")
                    if initial_node not in config['node']['peers']:
                        config['node']['peers'].insert(0, initial_node)
                else:
                    print_error(f"✗ Initial node {initial_node} returned status {response.status_code}")
                    print_error("Cannot start node without connection to initial node")
                    sys.exit(1)
            except requests.exceptions.ConnectionError:
                print_error(f"✗ Failed to connect to initial node: {initial_node}")
                print_error("Cannot start node without connection to initial node")
                if args.test:
                    print_error("Make sure the test initial node (127.0.0.1:9999) is running")
                else:
                    print_error("Make sure the initial node (216.255.208.105:9999) is running")
                sys.exit(1)
            except requests.exceptions.Timeout:
                print_error(f"✗ Timeout connecting to initial node: {initial_node}")
                print_error("Cannot start node without connection to initial node")
                sys.exit(1)
            except Exception as e:
                print_error(f"✗ Error connecting to initial node: {e}")
                print_error("Cannot start node without connection to initial node")
                sys.exit(1)
        is_initial_node = args.init
        node = Node(config, is_initial_node=is_initial_node)
        if args.genesis:
            try:
                print_info("Creating genesis block...")
                node.blockchain.create_genesis_block()
                print_success("Genesis block created successfully")
                return
            except Exception as e:
                print_error(f"Failed to create genesis block: {e}")
                sys.exit(1)
        node.start()
    except KeyboardInterrupt:
        print_warning("\nNode shutdown initiated by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 