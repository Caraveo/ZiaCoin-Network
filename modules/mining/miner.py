import hashlib
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import threading
from ..storage import ChainStorage
from ..encryption import Encryption

@dataclass
class Block:
    index: int
    timestamp: str
    transactions: List[Dict[str, Any]]
    previous_hash: str
    nonce: int
    hash: str
    difficulty: int
    merkle_root: str

class Miner:
    def __init__(self, storage: ChainStorage, target_block_time: int = 60, difficulty: int = 4, reward: int = 50):
        self.storage = storage
        self.target_block_time = target_block_time  # Target time between blocks in seconds
        self.current_difficulty = difficulty
        self.reward = reward
        self.mining = False
        self.current_block = None
        self.lock = threading.Lock()
        self._load_chain_state()

    def _load_chain_state(self):
        """Load the current chain state."""
        state = self.storage.load_chain_state()
        if state:
            self.current_difficulty = state.get('difficulty', 4)
            self.last_block_hash = state.get('latest_block_hash')
            self.height = state.get('height', 0)
        else:
            self.current_difficulty = 4
            self.last_block_hash = None
            self.height = 0

    def _calculate_merkle_root(self, transactions: List[Dict[str, Any]]) -> str:
        """Calculate the Merkle root of transactions."""
        if not transactions:
            return hashlib.sha256(b'').hexdigest()

        # Convert transactions to hashes
        hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                 for tx in transactions]

        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_hashes

        return hashes[0]

    def _adjust_difficulty(self, block_time: float):
        """Adjust mining difficulty based on block time."""
        if block_time < self.target_block_time * 0.5:
            self.current_difficulty += 1
        elif block_time > self.target_block_time * 2:
            self.current_difficulty = max(1, self.current_difficulty - 1)

    def _create_block(self, transactions: List[Dict[str, Any]]) -> Block:
        """Create a new block with the given transactions."""
        timestamp = datetime.utcnow().isoformat()
        merkle_root = self._calculate_merkle_root(transactions)
        
        return Block(
            index=self.height + 1,
            timestamp=timestamp,
            transactions=transactions,
            previous_hash=self.last_block_hash or '0' * 64,
            nonce=0,
            hash='',
            difficulty=self.current_difficulty,
            merkle_root=merkle_root
        )

    def _calculate_block_hash(self, block: Block) -> str:
        """Calculate the hash of a block."""
        block_data = {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': block.transactions,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'difficulty': block.difficulty,
            'merkle_root': block.merkle_root
        }
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()

    def _is_valid_hash(self, hash_value: str, difficulty: int) -> bool:
        """Check if a hash meets the difficulty requirement."""
        return hash_value.startswith('0' * difficulty)

    def mine_block(self, transactions: List[Dict[str, Any]]) -> Optional[Block]:
        """Mine a new block with the given transactions."""
        start_time = time.time()
        block = self._create_block(transactions)
        
        while True:
            block.nonce += 1
            block.hash = self._calculate_block_hash(block)
            
            if self._is_valid_hash(block.hash, block.difficulty):
                block_time = time.time() - start_time
                self._adjust_difficulty(block_time)
                
                # Update chain state
                self.height = block.index
                self.last_block_hash = block.hash
                
                # Save block and update state
                self.storage.save_block(block.__dict__)
                self.storage.save_chain_state({
                    'height': self.height,
                    'latest_block_hash': self.last_block_hash,
                    'difficulty': self.current_difficulty
                })
                
                return block

    def start_mining(self, transaction_pool: List[Dict[str, Any]]):
        """Start mining process in a separate thread."""
        if self.mining:
            return
        
        self.mining = True
        self.current_block = None
        
        def mining_thread():
            while self.mining:
                with self.lock:
                    if transaction_pool:
                        block = self.mine_block(transaction_pool[:])
                        if block:
                            self.current_block = block
                            # Clear processed transactions
                            transaction_pool.clear()
        
        threading.Thread(target=mining_thread, daemon=True).start()

    def stop_mining(self):
        """Stop the mining process."""
        self.mining = False
        self.current_block = None

    def get_mining_status(self) -> Dict[str, Any]:
        """Get current mining status."""
        return {
            'mining': self.mining,
            'difficulty': self.current_difficulty,
            'height': self.height,
            'latest_block': self.current_block.__dict__ if self.current_block else None
        }

def main():
    # Example usage
    storage = ChainStorage()
    miner = Miner(storage)
    
    # Example transactions
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
    
    try:
        while True:
            status = miner.get_mining_status()
            print(f"Mining status: {status}")
            time.sleep(5)
    except KeyboardInterrupt:
        miner.stop_mining()
        print("Mining stopped")

if __name__ == "__main__":
    main() 