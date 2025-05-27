import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from .chain_storage import ChainStorage

@pytest.fixture
def storage(tmp_path):
    """Create a temporary storage instance for testing."""
    chain_dir = tmp_path / "chain"
    storage = ChainStorage(str(chain_dir))
    yield storage
    # Cleanup after tests
    if chain_dir.exists():
        shutil.rmtree(chain_dir)

def test_directory_initialization(storage):
    """Test that directories are created properly."""
    assert storage.chain_dir.exists()
    assert storage.blocks_dir.exists()
    assert storage.wallets_dir.exists()

def test_save_and_load_block(storage):
    """Test saving and loading blocks."""
    block = {
        'hash': 'test_hash',
        'index': 1,
        'transactions': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Save block
    block_hash = storage.save_block(block)
    assert block_hash == 'test_hash'
    
    # Load block
    loaded_block = storage.load_block('test_hash')
    assert loaded_block is not None
    assert loaded_block['hash'] == block['hash']
    assert loaded_block['index'] == block['index']
    assert 'saved_at' in loaded_block

def test_save_and_load_chain_state(storage):
    """Test saving and loading chain state."""
    state = {
        'height': 1,
        'latest_block_hash': 'test_hash',
        'difficulty': 4
    }
    
    # Save state
    storage.save_chain_state(state)
    
    # Load state
    loaded_state = storage.load_chain_state()
    assert loaded_state is not None
    assert loaded_state['height'] == state['height']
    assert loaded_state['latest_block_hash'] == state['latest_block_hash']
    assert loaded_state['difficulty'] == state['difficulty']

def test_save_and_load_wallet(storage):
    """Test saving and loading wallet data."""
    wallet_data = {
        'address': 'test_address',
        'private_key': 'test_private_key',
        'public_key': 'test_public_key'
    }
    
    # Save wallet
    storage.save_wallet('test_address', wallet_data)
    
    # Load wallet
    loaded_wallet = storage.load_wallet('test_address')
    assert loaded_wallet is not None
    assert loaded_wallet['address'] == wallet_data['address']
    assert loaded_wallet['private_key'] == wallet_data['private_key']
    assert loaded_wallet['public_key'] == wallet_data['public_key']

def test_backup_and_restore(storage):
    """Test chain backup and restore functionality."""
    # Create some test data
    block = {
        'hash': 'test_hash',
        'index': 1,
        'transactions': []
    }
    storage.save_block(block)
    
    state = {'height': 1, 'latest_block_hash': 'test_hash'}
    storage.save_chain_state(state)
    
    # Create backup
    backup_name = 'test_backup'
    storage.backup_chain(backup_name)
    
    # Verify backup exists
    backup_dir = storage.chain_dir.parent / f"chain_backup_{backup_name}"
    assert backup_dir.exists()
    
    # Modify original data
    storage.save_block({'hash': 'new_hash', 'index': 2, 'transactions': []})
    
    # Restore from backup
    storage.restore_chain(backup_name)
    
    # Verify data was restored
    loaded_block = storage.load_block('test_hash')
    assert loaded_block is not None
    assert loaded_block['hash'] == 'test_hash'
    
    # Cleanup backup
    shutil.rmtree(backup_dir)

def test_cleanup_old_blocks(storage):
    """Test cleanup of old blocks."""
    # Create multiple blocks
    for i in range(5):
        block = {
            'hash': f'test_hash_{i}',
            'index': i,
            'transactions': []
        }
        storage.save_block(block)
    
    # Set chain state
    state = {'height': 5, 'latest_block_hash': 'test_hash_4'}
    storage.save_chain_state(state)
    
    # Cleanup old blocks
    storage.cleanup_old_blocks(keep_last_n=3)
    
    # Verify only last 3 blocks remain
    block_files = list(storage.blocks_dir.glob("*.json"))
    assert len(block_files) == 3
    
    # Verify oldest blocks are removed
    assert not (storage.blocks_dir / "test_hash_0.json").exists()
    assert not (storage.blocks_dir / "test_hash_1.json").exists()
    
    # Verify newest blocks remain
    assert (storage.blocks_dir / "test_hash_2.json").exists()
    assert (storage.blocks_dir / "test_hash_3.json").exists()
    assert (storage.blocks_dir / "test_hash_4.json").exists()

def test_get_latest_block_hash(storage):
    """Test getting the latest block hash."""
    # Initially should be None
    assert storage.get_latest_block_hash() is None
    
    # Set state
    state = {'latest_block_hash': 'test_hash'}
    storage.save_chain_state(state)
    
    # Should return the latest hash
    assert storage.get_latest_block_hash() == 'test_hash'

def test_get_block_height(storage):
    """Test getting the current block height."""
    # Initially should be 0
    assert storage.get_block_height() == 0
    
    # Set state
    state = {'height': 5}
    storage.save_chain_state(state)
    
    # Should return the height
    assert storage.get_block_height() == 5

if __name__ == "__main__":
    pytest.main(['-v', 'test_chain_storage.py']) 