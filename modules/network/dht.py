import hashlib
import time
import asyncio
import random
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from ..storage import ChainStorage

@dataclass
class DHTNode:
    node_id: str
    host: str
    port: int
    last_seen: float
    version: str = "1.0.0"
    height: int = 0
    is_active: bool = True

class KademliaDHT:
    def __init__(self, node_id: str, host: str, port: int, k: int = 20, alpha: int = 3):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.k = k  # Number of nodes in each k-bucket
        self.alpha = alpha  # Number of parallel requests
        self.routing_table: Dict[int, Set[DHTNode]] = {i: set() for i in range(160)}  # 160-bit keyspace
        self.peer_store: Dict[str, List[DHTNode]] = {}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("KademliaDHT")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _get_bucket_index(self, node_id: str) -> int:
        """Calculate the k-bucket index for a node ID."""
        # XOR the node IDs and find the first differing bit
        xor = int(self.node_id, 16) ^ int(node_id, 16)
        if xor == 0:
            return 159
        return 159 - (xor.bit_length() - 1)

    async def add_node(self, node: DHTNode) -> None:
        """Add a node to the routing table."""
        async with self.lock:
            bucket_index = self._get_bucket_index(node.node_id)
            bucket = self.routing_table[bucket_index]
            
            if node in bucket:
                # Update last seen time
                node.last_seen = time.time()
                return
            
            if len(bucket) < self.k:
                bucket.add(node)
            else:
                # Check for inactive nodes
                inactive_nodes = {n for n in bucket if not n.is_active}
                if inactive_nodes:
                    bucket.remove(inactive_nodes.pop())
                    bucket.add(node)
                else:
                    # Ping the least recently seen node
                    oldest_node = min(bucket, key=lambda n: n.last_seen)
                    if not await self._ping_node(oldest_node):
                        bucket.remove(oldest_node)
                        bucket.add(node)

    async def _ping_node(self, node: DHTNode) -> bool:
        """Ping a node to check if it's still active."""
        try:
            # Implement actual ping logic here
            # For now, just return True
            return True
        except Exception as e:
            self.logger.error(f"Error pinging node {node.node_id}: {str(e)}")
            return False

    async def find_node(self, target_id: str) -> List[DHTNode]:
        """Find the k closest nodes to the target ID."""
        async with self.lock:
            bucket_index = self._get_bucket_index(target_id)
            closest_nodes = set()
            
            # Get nodes from the target bucket
            closest_nodes.update(self.routing_table[bucket_index])
            
            # Get nodes from adjacent buckets if needed
            for i in range(1, 160):
                if len(closest_nodes) >= self.k:
                    break
                    
                # Check buckets above and below
                if bucket_index + i < 160:
                    closest_nodes.update(self.routing_table[bucket_index + i])
                if bucket_index - i >= 0:
                    closest_nodes.update(self.routing_table[bucket_index - i])
            
            return sorted(
                closest_nodes,
                key=lambda n: int(n.node_id, 16) ^ int(target_id, 16)
            )[:self.k]

    async def store_peer(self, peer: DHTNode) -> None:
        """Store a peer in the DHT."""
        async with self.lock:
            if peer.node_id not in self.peer_store:
                self.peer_store[peer.node_id] = []
            self.peer_store[peer.node_id].append(peer)

    async def get_peers(self, target_id: str) -> List[DHTNode]:
        """Get peers associated with a target ID."""
        async with self.lock:
            return self.peer_store.get(target_id, [])

    async def remove_inactive_nodes(self) -> None:
        """Remove inactive nodes from the routing table."""
        async with self.lock:
            current_time = time.time()
            for bucket in self.routing_table.values():
                inactive_nodes = {
                    node for node in bucket
                    if current_time - node.last_seen > 3600  # 1 hour
                }
                bucket.difference_update(inactive_nodes)

    async def start(self) -> None:
        """Start the DHT node."""
        # Start maintenance tasks
        asyncio.create_task(self._maintain_routing_table())
        asyncio.create_task(self._maintain_peer_store())

    async def _maintain_routing_table(self) -> None:
        """Maintain the routing table by removing inactive nodes."""
        while True:
            await self.remove_inactive_nodes()
            await asyncio.sleep(300)  # Check every 5 minutes

    async def _maintain_peer_store(self) -> None:
        """Maintain the peer store by removing inactive peers."""
        while True:
            async with self.lock:
                current_time = time.time()
                for node_id, peers in self.peer_store.items():
                    self.peer_store[node_id] = [
                        peer for peer in peers
                        if current_time - peer.last_seen <= 3600
                    ]
            await asyncio.sleep(300)  # Check every 5 minutes

    def get_routing_table_size(self) -> int:
        """Get the total number of nodes in the routing table."""
        return sum(len(bucket) for bucket in self.routing_table.values())

    def get_peer_store_size(self) -> int:
        """Get the total number of peers in the peer store."""
        return sum(len(peers) for peers in self.peer_store.values())

async def main():
    # Example usage
    node_id = hashlib.sha256(b"test_node").hexdigest()
    dht = KademliaDHT(node_id, "127.0.0.1", 8333)
    await dht.start()
    
    # Add some test nodes
    for i in range(5):
        test_node = DHTNode(
            node_id=hashlib.sha256(f"test_node_{i}".encode()).hexdigest(),
            host="127.0.0.1",
            port=8333 + i,
            last_seen=time.time()
        )
        await dht.add_node(test_node)
    
    # Find nodes
    target_id = hashlib.sha256(b"target").hexdigest()
    closest_nodes = await dht.find_node(target_id)
    print(f"Found {len(closest_nodes)} closest nodes to {target_id}")

if __name__ == "__main__":
    asyncio.run(main()) 