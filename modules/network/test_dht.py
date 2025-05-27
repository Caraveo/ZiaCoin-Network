import pytest
import asyncio
import hashlib
import time
from .dht import KademliaDHT, DHTNode

@pytest.fixture
def dht():
    node_id = hashlib.sha256(b"test_node").hexdigest()
    return KademliaDHT(node_id, "127.0.0.1", 8333)

@pytest.mark.asyncio
async def test_node_addition(dht):
    """Test adding nodes to the DHT."""
    # Create test nodes
    nodes = []
    for i in range(5):
        node = DHTNode(
            node_id=hashlib.sha256(f"test_node_{i}".encode()).hexdigest(),
            host="127.0.0.1",
            port=8333 + i,
            last_seen=time.time()
        )
        nodes.append(node)
        await dht.add_node(node)
    
    # Check routing table size
    assert dht.get_routing_table_size() == 5

@pytest.mark.asyncio
async def test_node_finding(dht):
    """Test finding nodes in the DHT."""
    # Add test nodes
    nodes = []
    for i in range(10):
        node = DHTNode(
            node_id=hashlib.sha256(f"test_node_{i}".encode()).hexdigest(),
            host="127.0.0.1",
            port=8333 + i,
            last_seen=time.time()
        )
        nodes.append(node)
        await dht.add_node(node)
    
    # Find nodes
    target_id = hashlib.sha256(b"target").hexdigest()
    closest_nodes = await dht.find_node(target_id)
    
    # Check results
    assert len(closest_nodes) <= dht.k
    assert all(isinstance(node, DHTNode) for node in closest_nodes)

@pytest.mark.asyncio
async def test_peer_storage(dht):
    """Test storing and retrieving peers."""
    # Create and store a peer
    peer = DHTNode(
        node_id=hashlib.sha256(b"test_peer").hexdigest(),
        host="127.0.0.1",
        port=8333,
        last_seen=time.time()
    )
    await dht.store_peer(peer)
    
    # Retrieve peers
    stored_peers = await dht.get_peers(peer.node_id)
    assert len(stored_peers) == 1
    assert stored_peers[0].node_id == peer.node_id

@pytest.mark.asyncio
async def test_inactive_node_removal(dht):
    """Test removal of inactive nodes."""
    # Add an inactive node
    inactive_node = DHTNode(
        node_id=hashlib.sha256(b"inactive").hexdigest(),
        host="127.0.0.1",
        port=8333,
        last_seen=time.time() - 7200  # 2 hours ago
    )
    await dht.add_node(inactive_node)
    
    # Run maintenance
    await dht.remove_inactive_nodes()
    
    # Check if node was removed
    assert dht.get_routing_table_size() == 0

@pytest.mark.asyncio
async def test_concurrent_operations(dht):
    """Test concurrent DHT operations."""
    # Create multiple tasks
    tasks = []
    for i in range(10):
        node = DHTNode(
            node_id=hashlib.sha256(f"concurrent_node_{i}".encode()).hexdigest(),
            host="127.0.0.1",
            port=8333 + i,
            last_seen=time.time()
        )
        tasks.append(dht.add_node(node))
        tasks.append(dht.store_peer(node))
    
    # Run tasks concurrently
    await asyncio.gather(*tasks)
    
    # Check results
    assert dht.get_routing_table_size() == 10
    assert dht.get_peer_store_size() == 10

@pytest.mark.asyncio
async def test_bucket_management(dht):
    """Test k-bucket management."""
    # Add more nodes than k
    for i in range(dht.k + 5):
        node = DHTNode(
            node_id=hashlib.sha256(f"bucket_test_{i}".encode()).hexdigest(),
            host="127.0.0.1",
            port=8333 + i,
            last_seen=time.time()
        )
        await dht.add_node(node)
    
    # Check bucket sizes
    for bucket in dht.routing_table.values():
        assert len(bucket) <= dht.k

def main():
    pytest.main(['-v', 'test_dht.py'])

if __name__ == "__main__":
    main() 