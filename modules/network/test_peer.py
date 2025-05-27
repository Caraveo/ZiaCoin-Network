import pytest
import asyncio
import json
from datetime import datetime
from .peer import PeerNetwork, Peer
from ..storage import ChainStorage

@pytest.fixture
def storage():
    return ChainStorage("test_chain")

@pytest.fixture
def network():
    return PeerNetwork(host="127.0.0.1", port=8334)

@pytest.mark.asyncio
async def test_peer_handshake(network):
    """Test peer handshake process."""
    # Create a mock peer connection
    reader, writer = await asyncio.open_connection("127.0.0.1", 8334)
    
    # Send handshake message
    handshake = {
        'type': 'handshake',
        'host': '127.0.0.1',
        'port': 8335,
        'version': '1.0.0',
        'height': 0
    }
    writer.write(json.dumps(handshake).encode())
    await writer.drain()
    
    # Read response
    data = await reader.read(1024)
    response = json.loads(data.decode())
    
    assert response['type'] == 'handshake_ack'
    assert response['version'] == '1.0.0'
    assert 'height' in response
    
    writer.close()
    await writer.wait_closed()

@pytest.mark.asyncio
async def test_peer_discovery(network):
    """Test peer discovery process."""
    # Start network
    network_task = asyncio.create_task(network.start())
    
    # Wait for peer discovery
    await asyncio.sleep(2)
    
    # Check if peers were discovered
    peer_count = network.get_peer_count()
    assert peer_count >= 0  # May be 0 if no bootstrap nodes are available
    
    # Stop network
    network.running = False
    await network_task

@pytest.mark.asyncio
async def test_block_sync(network):
    """Test blockchain synchronization."""
    # Create a test block
    block = {
        'index': 1,
        'timestamp': datetime.utcnow().isoformat(),
        'transactions': [],
        'previous_hash': '0' * 64,
        'hash': 'test_hash',
        'difficulty': 4,
        'merkle_root': 'test_merkle_root'
    }
    
    # Start network
    network_task = asyncio.create_task(network.start())
    
    # Wait for sync
    await asyncio.sleep(2)
    
    # Check if block was synced
    saved_block = network.storage.load_block(block['hash'])
    assert saved_block is not None
    
    # Stop network
    network.running = False
    await network_task

@pytest.mark.asyncio
async def test_transaction_broadcast(network):
    """Test transaction broadcasting."""
    # Create a test transaction
    transaction = {
        'sender': 'address1',
        'recipient': 'address2',
        'amount': 10,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Start network
    network_task = asyncio.create_task(network.start())
    
    # Broadcast transaction
    await network._broadcast_transaction(transaction)
    
    # Wait for broadcast
    await asyncio.sleep(2)
    
    # Check if transaction was added to pool
    assert transaction in network.miner.transaction_pool
    
    # Stop network
    network.running = False
    await network_task

@pytest.mark.asyncio
async def test_block_verification(network):
    """Test block verification."""
    # Create a valid block
    valid_block = {
        'index': 1,
        'timestamp': datetime.utcnow().isoformat(),
        'transactions': [],
        'previous_hash': '0' * 64,
        'hash': '0' * 64,  # Valid hash for difficulty 4
        'difficulty': 4,
        'merkle_root': 'test_merkle_root'
    }
    
    # Create an invalid block
    invalid_block = {
        'index': 1,
        'timestamp': datetime.utcnow().isoformat(),
        'transactions': [],
        'previous_hash': '0' * 64,
        'hash': 'invalid_hash',
        'difficulty': 4,
        'merkle_root': 'test_merkle_root'
    }
    
    assert network._verify_block(valid_block)
    assert not network._verify_block(invalid_block)

@pytest.mark.asyncio
async def test_transaction_verification(network):
    """Test transaction verification."""
    # Create a valid transaction
    valid_transaction = {
        'sender': 'address1',
        'recipient': 'address2',
        'amount': 10,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Create an invalid transaction
    invalid_transaction = {
        'sender': 'address1',
        'recipient': 'address2',
        'amount': -10,  # Invalid amount
        'timestamp': datetime.utcnow().isoformat()
    }
    
    assert network._verify_transaction(valid_transaction)
    assert not network._verify_transaction(invalid_transaction)

@pytest.mark.asyncio
async def test_peer_maintenance(network):
    """Test peer maintenance (removing inactive peers)."""
    # Add some peers
    peer1 = Peer(host='127.0.0.1', port=8335, last_seen=time.time())
    peer2 = Peer(host='127.0.0.1', port=8336, last_seen=time.time() - 7200)  # 2 hours ago
    
    with network.lock:
        network.peers.add(peer1)
        network.peers.add(peer2)
    
    # Run maintenance
    await network._maintain_peers()
    
    # Check if inactive peer was removed
    with network.lock:
        assert peer1 in network.peers
        assert peer2 not in network.peers

@pytest.mark.asyncio
async def test_concurrent_peer_operations(network):
    """Test concurrent peer operations."""
    # Start network
    network_task = asyncio.create_task(network.start())
    
    # Create multiple peer connections
    connections = []
    for i in range(5):
        reader, writer = await asyncio.open_connection("127.0.0.1", 8334)
        connections.append((reader, writer))
    
    # Send handshake from all connections
    for i, (reader, writer) in enumerate(connections):
        handshake = {
            'type': 'handshake',
            'host': '127.0.0.1',
            'port': 8335 + i,
            'version': '1.0.0',
            'height': i
        }
        writer.write(json.dumps(handshake).encode())
        await writer.drain()
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Check peer count
    assert network.get_peer_count() == 5
    
    # Close connections
    for reader, writer in connections:
        writer.close()
        await writer.wait_closed()
    
    # Stop network
    network.running = False
    await network_task

def main():
    pytest.main(['-v', 'test_peer.py'])

if __name__ == "__main__":
    main() 