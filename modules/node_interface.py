#!/usr/bin/env python3
"""
Node Interface Module for direct communication between wallet and node backend.
This module provides direct function calls when running on the same machine.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from modules.utils.print_utils import print_info, print_error, print_success

# Add the parent directory to the Python path to import node components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modules.blockchain.blockchain import Blockchain
    from modules.network.peer import PeerNetwork
    from modules.mining.miner import Miner
    from modules.wallet.wallet import WalletManager
    NODE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print_error(f"Node components not available: {e}")
    NODE_COMPONENTS_AVAILABLE = False

class NodeInterface:
    """Interface for direct communication with node backend components."""
    
    def __init__(self):
        self.blockchain = None
        self.peer_network = None
        self.miner = None
        self.wallet_manager = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the node interface by loading components."""
        if not NODE_COMPONENTS_AVAILABLE:
            print_error("Node components not available")
            return False
            
        try:
            # Load configuration
            config = self._load_config()
            
            # Initialize blockchain
            self.blockchain = Blockchain()
            if not self.blockchain.initialize():
                print_error("Failed to initialize blockchain")
                return False
                
            # Initialize wallet manager
            wallet_path = config.get('wallet', {}).get('storage_path', 'chain/wallets/')
            self.wallet_manager = WalletManager(storage_path=wallet_path)
            if not self.wallet_manager.initialize():
                print_error("Failed to initialize wallet manager")
                return False
                
            self._initialized = True
            print_success("Node interface initialized successfully")
            return True
            
        except Exception as e:
            print_error(f"Failed to initialize node interface: {e}")
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load node configuration."""
        try:
            if os.path.exists('node.conf'):
                with open('node.conf', 'r') as f:
                    return json.load(f)
            else:
                # Return default config
                return {
                    "node": {
                        "host": "localhost",
                        "port": 9999,
                        "peers": []
                    },
                    "blockchain": {
                        "difficulty": 4,
                        "mining_reward": 50,
                        "block_time": 60
                    },
                    "wallet": {
                        "storage_path": "chain/wallets/"
                    }
                }
        except Exception as e:
            print_error(f"Failed to load config: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get node status."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            return {
                'status': 'running',
                'node_type': 'local',
                'host': 'localhost',
                'port': 9999,
                'block_height': len(self.blockchain.chain),
                'peer_count': 0,  # Local mode
                'peers': [],
                'pending_transactions': len(self.blockchain.pending_transactions),
                'mining_difficulty': 4,
                'mining_reward': 50,
                'is_initial_node': True,
                'connection_type': 'direct'
            }
        except Exception as e:
            return {"error": f"Failed to get status: {e}"}
    
    def get_balance(self, address: str) -> Dict[str, Any]:
        """Get wallet balance."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            balance = self.blockchain.get_balance(address)
            return {'balance': balance}
        except Exception as e:
            return {"error": f"Failed to get balance: {e}"}
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            from modules.blockchain.blockchain import Transaction
            
            # Validate transaction data
            required_fields = ['sender', 'recipient', 'amount', 'private_key']
            if not all(field in transaction_data for field in required_fields):
                return {"error": "Missing required transaction fields"}
            
            # Create transaction
            transaction = Transaction(
                sender=transaction_data['sender'],
                recipient=transaction_data['recipient'],
                amount=float(transaction_data['amount'])
            )
            transaction.sign(transaction_data['private_key'])
            
            # Add to blockchain
            transaction_index = self.blockchain.add_transaction(transaction)
            
            return {
                'message': 'Transaction added to pool',
                'transaction': transaction.to_dict(),
                'transaction_index': transaction_index
            }
        except Exception as e:
            return {"error": f"Failed to create transaction: {e}"}
    
    def get_chain(self) -> Dict[str, Any]:
        """Get the full blockchain."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            return {
                'chain': [block.to_dict() for block in self.blockchain.chain],
                'length': len(self.blockchain.chain)
            }
        except Exception as e:
            return {"error": f"Failed to get chain: {e}"}
    
    def get_peers(self) -> Dict[str, Any]:
        """Get peer information."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            return {
                'peer_count': 0,
                'peers': [],
                'node_type': 'local',
                'host': 'localhost',
                'port': 9999
            }
        except Exception as e:
            return {"error": f"Failed to get peers: {e}"}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            return {
                'network_status': 'active',
                'node_type': 'local',
                'node_address': 'localhost:9999',
                'total_peers': 0,
                'active_peers': 0,
                'inactive_peers': 0,
                'peer_details': [],
                'blockchain_height': len(self.blockchain.chain),
                'pending_transactions': len(self.blockchain.pending_transactions),
                'connection_type': 'direct'
            }
        except Exception as e:
            return {"error": f"Failed to get network info: {e}"}
    
    def health_check(self) -> Dict[str, Any]:
        """Health check."""
        if not self._initialized:
            return {"error": "Node interface not initialized"}
            
        try:
            return {
                'status': 'healthy',
                'connection_type': 'direct',
                'timestamp': __import__('time').time()
            }
        except Exception as e:
            return {"error": f"Health check failed: {e}"}

# Global instance
_node_interface = None

def get_node_interface() -> Optional[NodeInterface]:
    """Get the global node interface instance."""
    global _node_interface
    if _node_interface is None:
        _node_interface = NodeInterface()
        if not _node_interface.initialize():
            return None
    return _node_interface

def is_local_node_available() -> bool:
    """Check if local node is available."""
    try:
        interface = get_node_interface()
        return interface is not None and interface._initialized
    except Exception:
        return False 