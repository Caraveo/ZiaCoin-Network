#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
from typing import List, Optional

from modules.network.peer import PeerNetwork
from modules.blockchain.blockchain import Blockchain
from modules.mining.miner import Miner
from modules.wallet.wallet import WalletManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, port: int = 8333, bootstrap_nodes: Optional[List[str]] = None):
        self.port = port
        self.bootstrap_nodes = bootstrap_nodes or []
        self.blockchain = Blockchain()
        self.peer_network = PeerNetwork(self.blockchain)
        self.miner = Miner(self.blockchain)
        self.wallet_manager = WalletManager()

    async def start(self):
        """Start the node and all its components."""
        try:
            # Start peer network
            await self.peer_network.start(self.port, self.bootstrap_nodes)
            logger.info(f"Node started on port {self.port}")
            
            # Connect to bootstrap nodes
            if self.bootstrap_nodes:
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

def load_config() -> dict:
    """Load configuration from chain.config file."""
    try:
        if os.path.exists('chain.config'):
            with open('chain.config', 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

async def main():
    parser = argparse.ArgumentParser(description='ZiaCoin Node')
    parser.add_argument('--port', type=int, help='Port to run the node on')
    parser.add_argument('--bootstrap-nodes', type=str, help='Comma-separated list of bootstrap nodes (host:port)')
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Use command line args or config values
    port = args.port or config.get('network', {}).get('port', 8333)
    bootstrap_nodes = args.bootstrap_nodes.split(',') if args.bootstrap_nodes else config.get('network', {}).get('bootstrap_nodes', [])

    # Create and start node
    node = Node(port=port, bootstrap_nodes=bootstrap_nodes)
    
    try:
        await node.start()
    except KeyboardInterrupt:
        logger.info("Shutting down node...")
        await node.stop()

if __name__ == "__main__":
    asyncio.run(main()) 