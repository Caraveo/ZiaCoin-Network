import sys
import os
import json
import hashlib
import time  # Use the module, not the function
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

from ..storage import ChainStorage
from ..mining.miner import Miner
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float
    timestamp: float = time.time()
    signature: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    def sign(self, private_key: str) -> None:
        """Sign the transaction with the sender's private key."""
        try:
            private_key_bytes = bytes.fromhex(private_key)
            private_key_obj = ec.derive_private_key(
                int.from_bytes(private_key_bytes, 'big'),
                ec.SECP256K1(),
                default_backend()
            )
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            signature = private_key_obj.sign(
                transaction_data,
                ec.ECDSA(hashes.SHA256())
            )
            self.signature = signature.hex()
        except Exception as e:
            raise ValueError(f"Failed to sign transaction: {str(e)}")

    def verify(self) -> bool:
        """Verify the transaction signature."""
        if not self.signature:
            return False
        try:
            public_key_bytes = bytes.fromhex(self.sender)  # Assuming sender is the public key
            public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(
                public_key_bytes,
                ec.SECP256K1()
            )
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            public_key_obj.verify(
                bytes.fromhex(self.signature),
                transaction_data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False

@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    difficulty: int = 4  # Number of leading zeros required
    merkle_root: str = ""  # Added merkle_root field
    block_hash: str = ""  # Store the calculated hash

    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash(),
            'merkle_root': self.merkle_root
        }

    def hash(self) -> str:
        """Calculate the block's hash."""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': str(self.timestamp),
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self) -> None:
        """Mine the block by finding a valid nonce."""
        target = '0' * self.difficulty
        while True:
            if self.hash()[:self.difficulty] == target:
                break
            self.nonce += 1

    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """Create a Block instance from a dictionary."""
        # Convert transaction dicts back to Transaction objects
        transactions = []
        for tx_data in data.get('transactions', []):
            if isinstance(tx_data, dict):
                tx = Transaction(
                    sender=tx_data.get('sender', ''),
                    recipient=tx_data.get('recipient', ''),
                    amount=tx_data.get('amount', 0.0),
                    timestamp=tx_data.get('timestamp', time.time()),
                    signature=tx_data.get('signature')
                )
                transactions.append(tx)
            else:
                transactions.append(tx_data)
        
        return cls(
            index=data.get('index', 0),
            timestamp=data.get('timestamp', time.time()),
            transactions=transactions,
            previous_hash=data.get('previous_hash', ''),
            nonce=data.get('nonce', 0),
            difficulty=data.get('difficulty', 4),
            merkle_root=data.get('merkle_root', ''),
            block_hash=data.get('hash', '')
        )

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.storage = ChainStorage()
        self.initialize()

    def initialize(self) -> bool:
        """Initialize the blockchain."""
        try:
            # Try to load existing chain from ChainStorage first
            existing_blocks = self.storage.load_chain()
            if existing_blocks:
                # Convert block dicts back to Block objects
                self.chain = [Block.from_dict(block) for block in existing_blocks]
                print_success(f"Blockchain loaded from ChainStorage: {len(self.chain)} blocks")
            else:
                # Check if old blockchain.json exists and migrate it
                if os.path.exists('blockchain.json'):
                    print_info("Found old blockchain.json, migrating to new format...")
                    self._migrate_from_old_format()
                else:
                    # Create new chain if none exists
                    self.create_genesis_block()
                    print_success("New blockchain initialized")
            
            # Load pending transactions from chain state
            chain_state = self.storage.load_chain_state()
            if chain_state:
                self.pending_transactions = chain_state.get('pending_transactions', [])
            
            return True
        except Exception as e:
            print_error(f"Failed to initialize blockchain: {e}")
            return False

    def _migrate_from_old_format(self) -> bool:
        """Migrate from old blockchain.json format to new ChainStorage format."""
        try:
            # Load old format
            with open('blockchain.json', 'r') as f:
                data = json.load(f)
            
            # Convert blocks to new format
            old_blocks = data.get('chain', [])
            for block_data in old_blocks:
                block = Block.from_dict(block_data)
                self.chain.append(block)
                # Save to new storage
                self.storage.save_block(block_data)
            
            # Save chain state
            chain_state = {
                'height': len(self.chain) - 1 if self.chain else 0,
                'latest_block_hash': self.chain[-1].block_hash if self.chain else None,
                'difficulty': self.chain[-1].difficulty if self.chain else 4,
                'pending_transactions': data.get('pending_transactions', []),
                'migrated_at': time.time()
            }
            self.storage.save_chain_state(chain_state)
            
            # Create backup of old file
            backup_file = f"blockchain_backup_{int(time.time())}.json"
            import shutil
            shutil.copy2('blockchain.json', backup_file)
            
            print_success(f"Migrated {len(old_blocks)} blocks to new format")
            print_success(f"Old file backed up as: {backup_file}")
            return True
        except Exception as e:
            print_error(f"Migration failed: {e}")
            return False

    def save_state(self) -> bool:
        """Save the current state of the blockchain using ChainStorage."""
        try:
            # Save each block to ChainStorage
            for block in self.chain:
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in block.transactions],
                    'previous_hash': block.previous_hash,
                    'nonce': block.nonce,
                    'difficulty': block.difficulty,
                    'merkle_root': block.merkle_root,
                    'hash': block.block_hash if block.block_hash else block.hash()
                }
                self.storage.save_block(block_data)
            
            # Save chain state
            chain_state = {
                'height': len(self.chain) - 1 if self.chain else 0,
                'latest_block_hash': self.chain[-1].block_hash if self.chain else None,
                'difficulty': self.chain[-1].difficulty if self.chain else 4,
                'pending_transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.pending_transactions],
                'last_saved': time.time()
            }
            self.storage.save_chain_state(chain_state)
            
            print_success("Blockchain state saved to ChainStorage")
            return True
        except Exception as e:
            print_error(f"Failed to save blockchain state: {e}")
            return False

    def create_genesis_block(self) -> None:
        """Create the first block in the chain."""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash='0' * 64,
            nonce=0
        )
        genesis_block.block_hash = genesis_block.hash()
        self.chain.append(genesis_block)
        print_success("Genesis block created")

    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain."""
        try:
            if self.is_chain_valid():
                self.chain.append(block)
                # Save block to ChainStorage immediately
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in block.transactions],
                    'previous_hash': block.previous_hash,
                    'nonce': block.nonce,
                    'difficulty': block.difficulty,
                    'merkle_root': block.merkle_root,
                    'hash': block.block_hash if block.block_hash else block.hash()
                }
                self.storage.save_block(block_data)
                self.save_state()
                return True
            return False
        except Exception as e:
            print_error(f"Failed to add block: {e}")
            return False

    def is_chain_valid(self) -> bool:
        """Verify the integrity of the blockchain."""
        try:
            for i in range(1, len(self.chain)):
                current_block = self.chain[i]
                previous_block = self.chain[i-1]

                # Verify current block's hash
                if current_block.block_hash != current_block.hash():
                    print_warning(f"Invalid hash in block {i}")
                    return False

                # Verify block's previous hash
                if current_block.previous_hash != previous_block.block_hash:
                    print_warning(f"Invalid previous hash in block {i}")
                    return False

            return True
        except Exception as e:
            print_error(f"Chain validation failed: {e}")
            return False

    def recover_chain(self) -> bool:
        """Attempt to recover the blockchain from corruption."""
        try:
            # Try to recover from ChainStorage backup first
            if hasattr(self.storage, 'backup_chain'):
                try:
                    self.storage.restore_chain('backup')
                    print_success("Blockchain recovered from ChainStorage backup")
                    return True
                except:
                    pass
            
            # Try to load from old backup if available
            if os.path.exists('blockchain.json.backup'):
                with open('blockchain.json.backup', 'r') as f:
                    data = json.load(f)
                    self.chain = [Block.from_dict(block) for block in data.get('chain', [])]
                    self.pending_transactions = data.get('pending_transactions', [])
                    # Migrate to new format
                    self._migrate_from_old_format()
                print_success("Blockchain recovered from old backup and migrated")
                return True
            
            print_warning("No backup found for recovery")
            return False
        except Exception as e:
            print_error(f"Chain recovery failed: {e}")
            return False

    def add_transaction(self, transaction: Transaction) -> int:
        """Add a new transaction to the pending transactions."""
        if not transaction.verify():
            raise ValueError("Invalid transaction signature")
        self.pending_transactions.append(transaction)
        return self.get_latest_block().index + 1

    def mine_pending_transactions(self) -> Block:
        """Mine a new block with pending transactions."""
        if not self.pending_transactions:
            raise ValueError("No pending transactions to mine")

        previous_block = self.get_latest_block()
        new_block = Block(
            index=previous_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions,
            previous_hash=previous_block.block_hash,
            nonce=0,
            difficulty=self.difficulty
        )

        new_block.mine_block()
        self.chain.append(new_block)
        
        # Save new block to ChainStorage immediately
        block_data = {
            'index': new_block.index,
            'timestamp': new_block.timestamp,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in new_block.transactions],
            'previous_hash': new_block.previous_hash,
            'nonce': new_block.nonce,
            'difficulty': new_block.difficulty,
            'merkle_root': new_block.merkle_root,
            'hash': new_block.block_hash if new_block.block_hash else new_block.hash()
        }
        self.storage.save_block(block_data)
        
        self.pending_transactions = []
        return new_block

    def get_chain(self) -> List[Dict]:
        """Get the entire blockchain."""
        return [block.to_dict() for block in self.chain]

    def get_balance(self, address: str) -> float:
        """Calculate the balance of an address."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address:
                    balance -= tx.amount
                if tx.recipient == address:
                    balance += tx.amount
        return balance

    def verify_chain(self) -> bool:
        """Verify the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # Verify block hash
            if current.hash() != current.hash():
                return False

            # Verify previous hash
            if current.previous_hash != previous.block_hash:
                return False

        return True 