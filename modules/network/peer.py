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
from ..mining import Miner
from .dht import KademliaDHT, DHTNode

@dataclass
class Peer:
    host: str
    port: int
    last_seen: float
    version: str = "1.0.0"
    height: int = 0
    is_active: bool = True

class PeerNetwork:
    def __init__(self, host: str = "0.0.0.0", port: int = 8333, bootstrap_nodes: List[Dict[str, Any]] = None):
        self.host = host
        self.port = port
        self.node_id = hashlib.sha256(f"{host}:{port}".encode()).hexdigest()
        self.peers: Set[Peer] = set()
        self.bootstrap_nodes = bootstrap_nodes or [
            {"host": "seed1.ziacoin.net", "port": 8333},
            {"host": "seed2.ziacoin.net", "port": 8333}
        ]
        self.storage = ChainStorage()
        self.miner = Miner(self.storage)
        self.lock = threading.Lock()
        self.running = False
        self.logger = logging.getLogger("PeerNetwork")
        
        # Initialize DHT
        self.dht = KademliaDHT(self.node_id, host, port)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    async def start(self):
        """Start the peer network."""
        self.running = True
        
        # Start DHT
        await self.dht.start()
        
        # Start server
        server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port
        )
        
        self.logger.info(f"Peer server started on {self.host}:{self.port}")
        
        # Start peer discovery
        asyncio.create_task(self._discover_peers())
        
        # Start peer maintenance
        asyncio.create_task(self._maintain_peers())
        
        # Start blockchain sync
        asyncio.create_task(self._sync_blockchain())
        
        async with server:
            await server.serve_forever()

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