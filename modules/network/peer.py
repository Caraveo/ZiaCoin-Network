import socket
import json
import threading
import time
import random
import hashlib
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
import logging
from ..storage import ChainStorage
from ..mining.miner import Miner
from .dht import KademliaDHT, DHTNode
import os
import requests
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

@dataclass
class Peer:
    host: str
    port: int
    last_seen: float
    version: str = "1.0.0"
    height: int = 0
    is_active: bool = True

class PeerNetwork:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.peers = set()
        self.is_running = False
        self.sync_thread = None
        self.host = "0.0.0.0"
        self.port = 8333
        self.node_id = hashlib.sha256(f"{self.host}:{self.port}".encode()).hexdigest()
        self.bootstrap_nodes = [
            {"host": "seed1.ziacoin.net", "port": 8333},
            {"host": "seed2.ziacoin.net", "port": 8333}
        ]
        self.storage = ChainStorage()
        self.miner = Miner(self.storage)
        self.lock = threading.Lock()
        self.running = False
        self.logger = logging.getLogger("PeerNetwork")
        
        # Initialize DHT
        self.dht = KademliaDHT(self.node_id, self.host, self.port)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def initialize(self) -> bool:
        """Initialize the peer network."""
        try:
            # Clear existing peers
            self.peers.clear()
            self.is_running = False
            
            # Load known peers from storage if available
            if os.path.exists('peers.json'):
                with open('peers.json', 'r') as f:
                    self.peers = set(json.load(f))
                print_success(f"Loaded {len(self.peers)} known peers")
            
            print_success("Peer network initialized")
            return True
        except Exception as e:
            print_error(f"Failed to initialize peer network: {e}")
            return False

    def start(self, port: int, bootstrap_nodes: List[str] = None) -> None:
        """Start the peer network."""
        if self.is_running:
            print_warning("Peer network already running")
            return

        self.is_running = True
        self.sync_thread = threading.Thread(
            target=self._sync_loop,
            args=(port, bootstrap_nodes)
        )
        self.sync_thread.daemon = True
        self.sync_thread.start()
        print_success(f"Peer network started on port {port}")

    def stop(self) -> None:
        """Stop the peer network."""
        try:
            if self.is_running:
                self.is_running = False
                if self.sync_thread:
                    self.sync_thread.join(timeout=5)
                
                # Save current peers
                with open('peers.json', 'w') as f:
                    json.dump(list(self.peers), f)
                
                print_success("Peer network stopped")
        except Exception as e:
            print_error(f"Error stopping peer network: {e}")

    def _sync_loop(self, port: int, bootstrap_nodes: List[str] = None) -> None:
        """Main synchronization loop."""
        try:
            # Connect to bootstrap nodes
            if bootstrap_nodes:
                for node in bootstrap_nodes:
                    try:
                        host, node_port = node.split(':')
                        self._connect_to_peer(host, int(node_port))
                    except Exception as e:
                        print_warning(f"Failed to connect to bootstrap node {node}: {e}")

            # Start periodic sync
            while self.is_running:
                self._sync_with_peers()
                time.sleep(30)  # Sync every 30 seconds
        except Exception as e:
            print_error(f"Sync loop error: {e}")
            self.is_running = False

    def _connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer node."""
        try:
            peer = f"{host}:{port}"
            if peer not in self.peers:
                # Verify peer is reachable
                response = requests.get(
                    f"http://{peer}/status",
                    timeout=5
                )
                if response.status_code == 200:
                    self.peers.add(peer)
                    print_success(f"Connected to peer: {peer}")
                    return True
            return False
        except Exception as e:
            print_warning(f"Failed to connect to peer {host}:{port}: {e}")
            return False

    def _sync_with_peers(self) -> None:
        """Synchronize blockchain with peers."""
        try:
            for peer in list(self.peers):
                try:
                    # Get peer's chain
                    response = requests.get(
                        f"http://{peer}/chain",
                        timeout=5
                    )
                    if response.status_code == 200:
                        peer_chain = response.json()['chain']
                        if len(peer_chain) > len(self.blockchain.chain):
                            # Verify and update chain
                            if self._verify_chain(peer_chain):
                                self.blockchain.chain = peer_chain
                                print_success(f"Chain synchronized with peer {peer}")
                except Exception as e:
                    print_warning(f"Failed to sync with peer {peer}: {e}")
                    self.peers.remove(peer)
        except Exception as e:
            print_error(f"Sync error: {e}")

    def _verify_chain(self, chain: List[Dict]) -> bool:
        """Verify the integrity of a peer's chain."""
        try:
            for i in range(1, len(chain)):
                current_block = chain[i]
                previous_block = chain[i-1]

                # Verify block hash
                if current_block['hash'] != self._calculate_block_hash(current_block):
                    return False

                # Verify previous hash
                if current_block['previous_hash'] != previous_block['hash']:
                    return False

            return True
        except Exception as e:
            print_error(f"Chain verification failed: {e}")
            return False

    def _calculate_block_hash(self, block: Dict) -> str:
        """Calculate the hash of a block."""
        block_string = json.dumps({
            'index': block['index'],
            'timestamp': block['timestamp'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
            'nonce': block['nonce']
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming peer connections."""
        try:
            data = await reader.read(1024)
            message = json.loads(data.decode())
            
            if message['type'] == 'handshake':
                await self._handle_handshake(writer, message)
            elif message['type'] == 'get_peers':
                await self._handle_get_peers(writer)
            elif message['type'] == 'get_blocks':
                await self._handle_get_blocks(writer, message)
            elif message['type'] == 'new_block':
                await self._handle_new_block(message)
            elif message['type'] == 'new_transaction':
                await self._handle_new_transaction(message)
            
        except Exception as e:
            self.logger.error(f"Error handling connection: {str(e)}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_handshake(self, writer: asyncio.StreamWriter, message: Dict[str, Any]):
        """Handle peer handshake."""
        peer = Peer(
            host=message['host'],
            port=message['port'],
            last_seen=time.time(),
            version=message['version'],
            height=message['height']
        )
        
        with self.lock:
            self.peers.add(peer)
        
        response = {
            'type': 'handshake_ack',
            'version': '1.0.0',
            'height': self.miner.height
        }
        
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def _handle_get_peers(self, writer: asyncio.StreamWriter):
        """Handle peer list requests."""
        with self.lock:
            peer_list = [
                {
                    'host': peer.host,
                    'port': peer.port,
                    'version': peer.version,
                    'height': peer.height
                }
                for peer in self.peers
            ]
        
        response = {
            'type': 'peer_list',
            'peers': peer_list
        }
        
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def _handle_get_blocks(self, writer: asyncio.StreamWriter, message: Dict[str, Any]):
        """Handle block requests."""
        start_height = message.get('start_height', 0)
        end_height = message.get('end_height', self.miner.height)
        
        blocks = []
        for height in range(start_height, min(end_height + 1, self.miner.height + 1)):
            block = self.storage.load_block_by_height(height)
            if block:
                blocks.append(block)
        
        response = {
            'type': 'blocks',
            'blocks': blocks
        }
        
        writer.write(json.dumps(response).encode())
        await writer.drain()

    async def _handle_new_block(self, message: Dict[str, Any]):
        """Handle new block announcements."""
        block = message['block']
        
        # Verify block
        if self._verify_block(block):
            # Add block to chain
            self.storage.save_block(block)
            
            # Update chain state
            self.miner.height = block['index']
            self.miner.last_block_hash = block['hash']
            
            # Broadcast to other peers
            await self._broadcast_block(block)

    async def _handle_new_transaction(self, message: Dict[str, Any]):
        """Handle new transaction announcements."""
        transaction = message['transaction']
        
        # Verify transaction
        if self._verify_transaction(transaction):
            # Add to transaction pool
            self.miner.transaction_pool.append(transaction)
            
            # Broadcast to other peers
            await self._broadcast_transaction(transaction)

    def _verify_block(self, block: Dict[str, Any]) -> bool:
        """Verify a block's validity."""
        try:
            # Check block structure
            required_fields = ['index', 'timestamp', 'transactions', 'previous_hash', 'hash', 'difficulty', 'merkle_root']
            if not all(field in block for field in required_fields):
                return False
            
            # Verify block hash
            if block['hash'] != self.miner._calculate_block_hash(block):
                return False
            
            # Verify difficulty
            if not self.miner._is_valid_hash(block['hash'], block['difficulty']):
                return False
            
            # Verify previous hash
            if block['index'] > 1:
                previous_block = self.storage.load_block(block['previous_hash'])
                if not previous_block:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying block: {str(e)}")
            return False

    def _verify_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Verify a transaction's validity."""
        try:
            # Check transaction structure
            required_fields = ['sender', 'recipient', 'amount', 'timestamp']
            if not all(field in transaction for field in required_fields):
                return False
            
            # Verify amount is positive
            if transaction['amount'] <= 0:
                return False
            
            # Verify timestamp is recent
            tx_time = datetime.fromisoformat(transaction['timestamp'])
            if (datetime.utcnow() - tx_time).total_seconds() > 3600:  # 1 hour
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying transaction: {str(e)}")
            return False

    async def _discover_peers(self):
        """Discover new peers using DHT."""
        while self.running:
            try:
                # Try bootstrap nodes
                for node in self.bootstrap_nodes:
                    try:
                        bootstrap_node = DHTNode(
                            node_id=hashlib.sha256(f"{node['host']}:{node['port']}".encode()).hexdigest(),
                            host=node['host'],
                            port=node['port'],
                            last_seen=time.time()
                        )
                        await self.dht.add_node(bootstrap_node)
                        
                        # Get peers from bootstrap node
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"http://{node['host']}:{node['port']}/peers") as response:
                                if response.status == 200:
                                    data = await response.json()
                                    for peer_data in data['peers']:
                                        peer = DHTNode(
                                            node_id=hashlib.sha256(f"{peer_data['host']}:{peer_data['port']}".encode()).hexdigest(),
                                            host=peer_data['host'],
                                            port=peer_data['port'],
                                            last_seen=time.time(),
                                            version=peer_data['version'],
                                            height=peer_data['height']
                                        )
                                        await self.dht.add_node(peer)
                                        await self.dht.store_peer(peer)
                    except Exception as e:
                        self.logger.error(f"Error connecting to bootstrap node {node['host']}: {str(e)}")
                
                # Find more peers using DHT
                target_id = hashlib.sha256(str(time.time()).encode()).hexdigest()
                closest_nodes = await self.dht.find_node(target_id)
                
                for node in closest_nodes:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"http://{node.host}:{node.port}/peers") as response:
                                if response.status == 200:
                                    data = await response.json()
                                    for peer_data in data['peers']:
                                        peer = DHTNode(
                                            node_id=hashlib.sha256(f"{peer_data['host']}:{peer_data['port']}".encode()).hexdigest(),
                                            host=peer_data['host'],
                                            port=peer_data['port'],
                                            last_seen=time.time(),
                                            version=peer_data['version'],
                                            height=peer_data['height']
                                        )
                                        await self.dht.add_node(peer)
                                        await self.dht.store_peer(peer)
                    except Exception as e:
                        self.logger.error(f"Error getting peers from {node.host}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error in peer discovery: {str(e)}")
            
            await asyncio.sleep(300)  # Discover peers every 5 minutes

    async def _maintain_peers(self):
        """Maintain peer list using DHT."""
        while self.running:
            try:
                # Update peer list from DHT
                with self.lock:
                    self.peers = {
                        Peer(
                            host=node.host,
                            port=node.port,
                            last_seen=node.last_seen,
                            version=node.version,
                            height=node.height,
                            is_active=node.is_active
                        )
                        for node in self.dht.routing_table.values()
                        for node in bucket
                    }
            except Exception as e:
                self.logger.error(f"Error maintaining peers: {str(e)}")
            
            await asyncio.sleep(60)  # Check every minute

    async def _sync_blockchain(self):
        """Synchronize blockchain with peers."""
        while self.running:
            try:
                with self.lock:
                    peers_copy = self.peers.copy()
                
                for peer in peers_copy:
                    if peer.height > self.miner.height:
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(
                                    f"http://{peer.host}:{peer.port}/blocks",
                                    params={
                                        'start_height': self.miner.height + 1,
                                        'end_height': peer.height
                                    }
                                ) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        for block in data['blocks']:
                                            if self._verify_block(block):
                                                self.storage.save_block(block)
                                                self.miner.height = block['index']
                                                self.miner.last_block_hash = block['hash']
                        except Exception as e:
                            self.logger.error(f"Error syncing with peer {peer.host}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error in blockchain sync: {str(e)}")
            
            await asyncio.sleep(60)  # Sync every minute

    async def _broadcast_block(self, block: Dict[str, Any]):
        """Broadcast a new block to all peers."""
        message = {
            'type': 'new_block',
            'block': block
        }
        
        with self.lock:
            peers_copy = self.peers.copy()
        
        for peer in peers_copy:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"http://{peer.host}:{peer.port}/block",
                        json=message
                    ) as response:
                        if response.status != 200:
                            self.logger.warning(f"Failed to broadcast block to {peer.host}")
            except Exception as e:
                self.logger.error(f"Error broadcasting block to {peer.host}: {str(e)}")

    async def _broadcast_transaction(self, transaction: Dict[str, Any]):
        """Broadcast a new transaction to all peers."""
        message = {
            'type': 'new_transaction',
            'transaction': transaction
        }
        
        with self.lock:
            peers_copy = self.peers.copy()
        
        for peer in peers_copy:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"http://{peer.host}:{peer.port}/transaction",
                        json=message
                    ) as response:
                        if response.status != 200:
                            self.logger.warning(f"Failed to broadcast transaction to {peer.host}")
            except Exception as e:
                self.logger.error(f"Error broadcasting transaction to {peer.host}: {str(e)}")

    def get_peer_count(self) -> int:
        """Get the number of connected peers."""
        with self.lock:
            return len(self.peers)

    def get_peer_list(self) -> List[Dict[str, Any]]:
        """Get a list of all connected peers."""
        with self.lock:
            return [
                {
                    'host': peer.host,
                    'port': peer.port,
                    'version': peer.version,
                    'height': peer.height,
                    'last_seen': peer.last_seen
                }
                for peer in self.peers
            ]

async def main():
    # Example usage
    network = PeerNetwork()
    await network.start()

if __name__ == "__main__":
    asyncio.run(main()) 