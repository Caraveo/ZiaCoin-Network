import sys
import os
import json
import hashlib
from time import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

from ..storage import ChainStorage
from ..mining.miner import Miner

@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: float
    timestamp: float = time()
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

class Blockchain:
    def __init__(self):
        self.storage = ChainStorage()
        self.miner = Miner(self.storage)
        self.chain: List[Block] = [self.create_genesis_block()]
        self.difficulty = 4
        self.pending_transactions: List[Transaction] = []
        self._load_chain()

    def _load_chain(self):
        """Load the blockchain from storage."""
        self.chain = self.storage.load_chain()
        if not self.chain:
            self.chain = []
            # Create genesis block
            self._create_genesis_block()

    def _create_genesis_block(self):
        """Create the genesis block."""
        genesis_block = {
            'index': 0,
            'timestamp': time(),
            'transactions': [],
            'previous_hash': '0' * 64,
            'nonce': 0,
            'difficulty': 4,
            'merkle_root': hashlib.sha256(b'').hexdigest()
        }
        genesis_block['hash'] = self._calculate_block_hash(genesis_block)
        genesis_block.pop('hash', None)
        self.chain.append(Block(**genesis_block))
        genesis_block['hash'] = self._calculate_block_hash(genesis_block)
        self.storage.save_block(genesis_block)

    def _calculate_block_hash(self, block: Dict) -> str:
        """Calculate the hash of a block."""
        block_string = json.dumps({
            'index': block['index'],
            'timestamp': str(block['timestamp']),
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in block['transactions']],
            'previous_hash': block['previous_hash'],
            'nonce': block['nonce'],
            'difficulty': block['difficulty'],
            'merkle_root': block['merkle_root']
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def create_genesis_block() -> Block:
        """Create the first block in the chain."""
        return Block(
            index=0,
            timestamp=time(),
            transactions=[],
            previous_hash="0" * 64,
            nonce=0
        )

    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain."""
        return self.chain[-1]

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
            timestamp=time(),
            transactions=self.pending_transactions,
            previous_hash=previous_block.hash(),
            nonce=0,
            difficulty=self.difficulty
        )

        new_block.mine_block()
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self) -> bool:
        """Verify the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Verify block hash
            if current_block.hash() != current_block.hash():
                return False

            # Verify previous hash
            if current_block.previous_hash != previous_block.hash():
                return False

            # Verify all transactions
            for transaction in current_block.transactions:
                if not transaction.verify():
                    return False

        return True

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
            if current.previous_hash != previous.hash():
                return False

        return True 