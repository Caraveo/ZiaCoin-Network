import pytest
import time
from datetime import datetime
from .miner import Miner, Block
from ..storage import ChainStorage

@pytest.fixture
def storage():
    return ChainStorage("test_chain")

@pytest.fixture
def miner(storage):
    return Miner(storage, target_block_time=1)

def test_block_creation(miner):
    """Test block creation with transactions."""
    transactions = [
        {
            'sender': 'address1',
            'recipient': 'address2',
            'amount': 10,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    
    block = miner._create_block(transactions)
    assert block.index == 1
    assert block.previous_hash == '0' * 64
    assert len(block.transactions) == 1
    assert block.difficulty == 4
    assert block.merkle_root != ''

def test_merkle_root_calculation(miner):
    """Test Merkle root calculation for transactions."""
    transactions = [
        {'tx1': 'data1'},
        {'tx2': 'data2'},
        {'tx3': 'data3'}
    ]
    
    merkle_root = miner._calculate_merkle_root(transactions)
    assert merkle_root != ''
    assert len(merkle_root) == 64  # SHA-256 hash length
    
    # Test with empty transactions
    empty_root = miner._calculate_merkle_root([])
    assert empty_root != merkle_root

def test_difficulty_adjustment(miner):
    """Test mining difficulty adjustment."""
    # Test increasing difficulty
    miner._adjust_difficulty(0.2)  # Less than half target time
    assert miner.current_difficulty == 5
    
    # Test decreasing difficulty
    miner._adjust_difficulty(3)  # More than double target time
    assert miner.current_difficulty == 4
    
    # Test minimum difficulty
    miner.current_difficulty = 1
    miner._adjust_difficulty(3)
    assert miner.current_difficulty == 1

def test_block_hashing(miner):
    """Test block hash calculation and validation."""
    block = miner._create_block([])
    hash_value = miner._calculate_block_hash(block)
    
    assert len(hash_value) == 64
    assert miner._is_valid_hash(hash_value, 0)  # Should always be valid with difficulty 0
    assert not miner._is_valid_hash(hash_value, 1)  # Should not be valid with difficulty 1

def test_mining_process(miner):
    """Test the complete mining process."""
    transactions = [
        {
            'sender': 'address1',
            'recipient': 'address2',
            'amount': 10,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    
    # Start mining
    miner.start_mining(transactions)
    time.sleep(2)  # Wait for mining to start
    
    # Check mining status
    status = miner.get_mining_status()
    assert status['mining'] == True
    assert status['difficulty'] >= 4
    
    # Stop mining
    miner.stop_mining()
    status = miner.get_mining_status()
    assert status['mining'] == False

def test_block_persistence(miner, storage):
    """Test that mined blocks are properly saved."""
    transactions = [
        {
            'sender': 'address1',
            'recipient': 'address2',
            'amount': 10,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    
    # Mine a block
    block = miner.mine_block(transactions)
    assert block is not None
    
    # Verify block was saved
    saved_block = storage.load_block(block.hash)
    assert saved_block is not None
    assert saved_block['index'] == block.index
    assert saved_block['hash'] == block.hash

def test_chain_state_persistence(miner, storage):
    """Test that chain state is properly updated and saved."""
    transactions = [
        {
            'sender': 'address1',
            'recipient': 'address2',
            'amount': 10,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    
    # Mine a block
    block = miner.mine_block(transactions)
    
    # Verify chain state
    state = storage.load_chain_state()
    assert state is not None
    assert state['height'] == 1
    assert state['latest_block_hash'] == block.hash
    assert state['difficulty'] == miner.current_difficulty

def test_concurrent_mining(miner):
    """Test mining with multiple transactions."""
    transactions = [
        {
            'sender': f'address{i}',
            'recipient': f'address{i+1}',
            'amount': i,
            'timestamp': datetime.utcnow().isoformat()
        }
        for i in range(5)
    ]
    
    # Start mining
    miner.start_mining(transactions)
    time.sleep(2)
    
    # Add more transactions
    new_transactions = [
        {
            'sender': 'address6',
            'recipient': 'address7',
            'amount': 10,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
    transactions.extend(new_transactions)
    
    time.sleep(2)
    miner.stop_mining()
    
    status = miner.get_mining_status()
    assert status['mining'] == False
    assert status['height'] > 0

def main():
    pytest.main(['-v', 'test_miner.py'])

if __name__ == "__main__":
    main() 