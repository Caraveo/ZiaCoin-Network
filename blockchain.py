import json
import hashlib
from time import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

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

    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash()
        }

    def hash(self) -> str:
        """Calculate the block's hash."""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': str(self.timestamp),
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
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
        self.chain: List[Block] = [self.create_genesis_block()]
        self.difficulty = 4
        self.pending_transactions: List[Transaction] = []

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

def main():
    # Create a new blockchain
    blockchain = Blockchain()

    # Create some sample transactions
    try:
        # Create wallets first (using the Wallet class from wallet.py)
        from wallet import Wallet
        alice = Wallet.create()
        bob = Wallet.create()

        # Create and sign transactions
        tx1 = Transaction(alice.address, bob.address, 1.0)
        tx1.sign(alice.private_key)
        blockchain.add_transaction(tx1)

        # Mine the block
        mined_block = blockchain.mine_pending_transactions()
        print("\nMined Block:")
        print(json.dumps(mined_block.to_dict(), indent=4))

        # Verify chain
        print(f"\nIs chain valid? {blockchain.is_chain_valid()}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
