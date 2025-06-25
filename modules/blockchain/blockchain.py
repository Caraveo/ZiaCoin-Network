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
            # Load existing chain if available
            if os.path.exists('blockchain.json'):
                with open('blockchain.json', 'r') as f:
                    data = json.load(f)
                    self.chain = [Block.from_dict(block) for block in data.get('chain', [])]
                    self.pending_transactions = data.get('pending_transactions', [])
                    # Don't try to load storage from JSON
                print_success("Blockchain loaded from storage")
            else:
                # Create new chain if none exists
                self.create_genesis_block()
                print_success("New blockchain initialized")
            return True
        except Exception as e:
            print_error(f"Failed to initialize blockchain: {e}")
            return False

    def save_state(self) -> bool:
        """Save the current state of the blockchain."""
        try:
            # Create a safe copy of the chain data
            chain_data = []
            for block in self.chain:
                try:
                    block_dict = {
                        'index': block.index,
                        'timestamp': block.timestamp,
                        'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in block.transactions],
                        'previous_hash': block.previous_hash,
                        'nonce': block.nonce,
                        'difficulty': block.difficulty,
                        'merkle_root': block.merkle_root,
                        'hash': block.block_hash if block.block_hash else block.hash()
                    }
                    chain_data.append(block_dict)
                except Exception as e:
                    print_warning(f"Error serializing block {getattr(block, 'index', 'unknown')}: {e}")
                    continue
            
            # Create safe copy of pending transactions
            pending_data = []
            for tx in self.pending_transactions:
                try:
                    if hasattr(tx, 'to_dict'):
                        pending_data.append(tx.to_dict())
                    else:
                        pending_data.append(tx)
                except Exception as e:
                    print_warning(f"Error serializing transaction: {e}")
                    continue
            
            data = {
                'chain': chain_data,
                'pending_transactions': pending_data,
                'storage': {}  # Store empty dict instead of storage object
            }
            
            with open('blockchain.json', 'w') as f:
                json.dump(data, f, indent=4)
            print_success("Blockchain state saved")
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
            # Try to load from backup if available
            if os.path.exists('blockchain.json.backup'):
                with open('blockchain.json.backup', 'r') as f:
                    data = json.load(f)
                    self.chain = [Block.from_dict(block) for block in data.get('chain', [])]
                    self.pending_transactions = data.get('pending_transactions', [])
                    # Don't try to load storage from JSON
                print_success("Blockchain recovered from backup")
                return True
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