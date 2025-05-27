import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

class ChainStorage:
    def __init__(self, chain_dir: str = "chain"):
        self.chain_dir = Path(chain_dir)
        self.blocks_dir = self.chain_dir / "blocks"
        self.wallets_dir = self.chain_dir / "wallets"
        self.state_file = self.chain_dir / "state.json"
        self._initialize_directories()

    def _initialize_directories(self):
        """Create necessary directories if they don't exist."""
        self.chain_dir.mkdir(exist_ok=True)
        self.blocks_dir.mkdir(exist_ok=True)
        self.wallets_dir.mkdir(exist_ok=True)

    def save_block(self, block: Dict[str, Any]) -> str:
        """Save a block to disk."""
        block_hash = block['hash']
        block_file = self.blocks_dir / f"{block_hash}.json"
        
        # Add timestamp for when the block was saved
        block['saved_at'] = datetime.utcnow().isoformat()
        
        with open(block_file, 'w') as f:
            json.dump(block, f, indent=4)
        
        return block_hash

    def load_block(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Load a block from disk."""
        block_file = self.blocks_dir / f"{block_hash}.json"
        if not block_file.exists():
            return None
        
        with open(block_file, 'r') as f:
            return json.load(f)

    def save_chain_state(self, state: Dict[str, Any]):
        """Save the current chain state."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=4)

    def load_chain_state(self) -> Optional[Dict[str, Any]]:
        """Load the current chain state."""
        if not self.state_file.exists():
            return None
        
        with open(self.state_file, 'r') as f:
            return json.load(f)

    def save_wallet(self, address: str, wallet_data: Dict[str, Any]):
        """Save wallet data."""
        wallet_file = self.wallets_dir / f"{address}.json"
        
        # Encrypt sensitive data before saving
        if 'private_key' in wallet_data:
            wallet_data['private_key'] = self._encrypt_private_key(wallet_data['private_key'])
        
        with open(wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=4)

    def load_wallet(self, address: str) -> Optional[Dict[str, Any]]:
        """Load wallet data."""
        wallet_file = self.wallets_dir / f"{address}.json"
        if not wallet_file.exists():
            return None
        
        with open(wallet_file, 'r') as f:
            wallet_data = json.load(f)
            
            # Decrypt private key if present
            if 'private_key' in wallet_data:
                wallet_data['private_key'] = self._decrypt_private_key(wallet_data['private_key'])
            
            return wallet_data

    def get_latest_block_hash(self) -> Optional[str]:
        """Get the hash of the latest block."""
        state = self.load_chain_state()
        return state.get('latest_block_hash') if state else None

    def get_block_height(self) -> int:
        """Get the current block height."""
        state = self.load_chain_state()
        return state.get('height', 0) if state else 0

    def backup_chain(self, backup_name: str):
        """Create a backup of the entire chain."""
        backup_dir = self.chain_dir.parent / f"chain_backup_{backup_name}"
        shutil.copytree(self.chain_dir, backup_dir)

    def restore_chain(self, backup_name: str):
        """Restore chain from a backup."""
        backup_dir = self.chain_dir.parent / f"chain_backup_{backup_name}"
        if not backup_dir.exists():
            raise ValueError(f"Backup {backup_name} not found")
        
        # Remove current chain directory
        shutil.rmtree(self.chain_dir)
        
        # Restore from backup
        shutil.copytree(backup_dir, self.chain_dir)

    def _encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key before storage."""
        # TODO: Implement proper encryption
        # For now, just return the key as is
        return private_key

    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key after loading."""
        # TODO: Implement proper decryption
        # For now, just return the key as is
        return encrypted_key

    def cleanup_old_blocks(self, keep_last_n: int = 1000):
        """Remove old blocks while keeping the most recent ones."""
        state = self.load_chain_state()
        if not state:
            return
        
        current_height = state.get('height', 0)
        if current_height <= keep_last_n:
            return
        
        # Get all block files
        block_files = sorted(self.blocks_dir.glob("*.json"))
        
        # Keep only the most recent blocks
        for block_file in block_files[:-keep_last_n]:
            block_file.unlink()

def main():
    # Example usage
    storage = ChainStorage()
    
    # Save a block
    block = {
        'hash': 'test_hash',
        'index': 1,
        'transactions': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    storage.save_block(block)
    
    # Save chain state
    state = {
        'height': 1,
        'latest_block_hash': 'test_hash',
        'difficulty': 4
    }
    storage.save_chain_state(state)
    
    # Create backup
    storage.backup_chain('test_backup')
    
    print("Storage operations completed successfully")

if __name__ == "__main__":
    main() 