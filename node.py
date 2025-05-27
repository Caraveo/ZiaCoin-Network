#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
from typing import List, Optional, Dict, Any

from modules.network.peer import PeerNetwork
from modules.blockchain.blockchain import Blockchain
from modules.mining.miner import Miner
from modules.wallet.wallet import WalletManager
from modules.sync.sync import CodeSync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port = config['network']['port']
        self.bootstrap_nodes = config['network']['bootstrap_nodes']
        self.mining_difficulty = config['mining']['difficulty']
        self.mining_reward = config['mining']['reward']
        self.wallet_path = config['wallet']['storage_path']
        
        # Initialize components with config
        self.blockchain = Blockchain()
        self.peer_network = PeerNetwork(self.blockchain)
        self.miner = Miner(
            self.blockchain.storage,
            difficulty=self.mining_difficulty,
            reward=self.mining_reward
        )
        self.wallet_manager = WalletManager(storage_path=self.wallet_path)

    async def start(self):
        """Start the node and all its components."""
        try:
            # Start peer network
            await self.peer_network.start(self.port, self.bootstrap_nodes)
            logger.info(f"Node started on port {self.port}")
            logger.info(f"Mining difficulty: {self.mining_difficulty}")
            logger.info(f"Mining reward: {self.mining_reward}")
            logger.info(f"Wallet storage: {self.wallet_path}")
            
            # Connect to bootstrap nodes
            if self.bootstrap_nodes:
                logger.info(f"Connecting to bootstrap nodes: {self.bootstrap_nodes}")
                for node in self.bootstrap_nodes:
                    host, port = node.split(':')
                    await self.peer_network.connect_to_peer(host, int(port))
            
            # Start mining
            self.miner.start()
            logger.info("Mining started")
            
            # Keep the node running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting node: {e}")
            raise

    async def stop(self):
        """Stop the node and all its components."""
        try:
            self.miner.stop()
            await self.peer_network.stop()
            logger.info("Node stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping node: {e}")
            raise

def load_config() -> Dict[str, Any]:
    """Load and validate configuration from chain.config file."""
    default_config = {
        "network": {
            "port": 8333,
            "bootstrap_nodes": []
        },
        "mining": {
            "difficulty": 4,
            "reward": 50
        },
        "wallet": {
            "storage_path": "wallets/"
        }
    }
    
    try:
        if os.path.exists('chain.config'):
            with open('chain.config', 'r') as f:
                user_config = json.load(f)
                # Merge with defaults, keeping user values where provided
                for section in default_config:
                    if section in user_config:
                        default_config[section].update(user_config[section])
                logger.info("Loaded configuration from chain.config")
        else:
            logger.warning("No chain.config found, using default configuration")
            
        return default_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.warning("Using default configuration")
        return default_config

async def main():
    parser = argparse.ArgumentParser(description='ZiaCoin Node')
    parser.add_argument('--port', type=int, help='Override port from config')
    parser.add_argument('--bootstrap-nodes', type=str, help='Override bootstrap nodes from config (comma-separated host:port)')
    parser.add_argument('--genesis', action='store_true', help='Mine the first genesis block')
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Override config with command line args if provided
    if args.port:
        config['network']['port'] = args.port
    if args.bootstrap_nodes:
        config['network']['bootstrap_nodes'] = args.bootstrap_nodes.split(',')

    # Create and start node
    node = Node(config=config)
    
    if args.genesis:
        node.blockchain._create_genesis_block()
        logger.info("Genesis block mined successfully.")
        return

    try:
        await node.start()
    except KeyboardInterrupt:
        logger.info("Shutting down node...")
        await node.stop()

if __name__ == "__main__":
    asyncio.run(main()) 