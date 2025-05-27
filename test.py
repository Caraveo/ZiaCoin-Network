import pytest
from blockchain import Blockchain, Transaction, Block
from wallet import Wallet
import time
import json

@pytest.fixture
def blockchain():
    """Create a fresh blockchain instance for each test."""
    return Blockchain()

@pytest.fixture
def wallets():
    """Create two test wallets."""
    alice = Wallet.create()
    bob = Wallet.create()
    return alice, bob

def test_wallet_creation():
    """Test wallet creation and key generation."""
    wallet = Wallet.create()
    assert wallet.private_key is not None
    assert wallet.public_key is not None
    assert wallet.address is not None
    assert len(wallet.private_key) == 64  # 32 bytes in hex
    assert len(wallet.public_key) > 0
    assert len(wallet.address) > 0

def test_transaction_creation_and_signing(wallets):
    """Test transaction creation and signing."""
    alice, bob = wallets
    amount = 1.0
    
    # Create transaction
    transaction = Transaction(
        sender=alice.address,
        recipient=bob.address,
        amount=amount
    )
    
    # Sign transaction
    transaction.sign(alice.private_key)
    
    # Verify transaction
    assert transaction.signature is not None
    assert transaction.verify() is True
    
    # Test invalid signature
    transaction.signature = "invalid"
    assert transaction.verify() is False

def test_block_creation(blockchain):
    """Test block creation and mining."""
    # Create a new block
    block = Block(
        index=1,
        timestamp=time.time(),
        transactions=[],
        previous_hash=blockchain.chain[0].hash()
    )
    
    # Mine the block
    block.mine_block()
    
    # Verify block properties
    assert block.hash()[:block.difficulty] == '0' * block.difficulty
    assert block.nonce > 0

def test_blockchain_initialization(blockchain):
    """Test blockchain initialization."""
    assert len(blockchain.chain) == 1  # Genesis block
    assert blockchain.chain[0].index == 0
    assert blockchain.chain[0].previous_hash == "0" * 64
    assert len(blockchain.chain[0].transactions) == 0

def test_transaction_addition(blockchain, wallets):
    """Test adding transactions to the blockchain."""
    alice, bob = wallets
    
    # Create and sign transaction
    transaction = Transaction(
        sender=alice.address,
        recipient=bob.address,
        amount=1.0
    )
    transaction.sign(alice.private_key)
    
    # Add transaction to blockchain
    block_index = blockchain.add_transaction(transaction)
    assert block_index == 1  # Will be added to the next block
    assert len(blockchain.pending_transactions) == 1

def test_block_mining(blockchain, wallets):
    """Test mining blocks with transactions."""
    alice, bob = wallets
    
    # Create and add multiple transactions
    for i in range(3):
        transaction = Transaction(
            sender=alice.address,
            recipient=bob.address,
            amount=1.0
        )
        transaction.sign(alice.private_key)
        blockchain.add_transaction(transaction)
    
    # Mine block
    block = blockchain.mine_pending_transactions()
    
    # Verify block
    assert block.index == 1
    assert len(block.transactions) == 3
    assert len(blockchain.pending_transactions) == 0
    assert block.hash()[:block.difficulty] == '0' * block.difficulty

def test_chain_validation(blockchain, wallets):
    """Test blockchain validation."""
    alice, bob = wallets
    
    # Add some transactions and mine blocks
    for i in range(2):
        transaction = Transaction(
            sender=alice.address,
            recipient=bob.address,
            amount=1.0
        )
        transaction.sign(alice.private_key)
        blockchain.add_transaction(transaction)
        blockchain.mine_pending_transactions()
    
    # Verify chain
    assert blockchain.is_chain_valid() is True
    
    # Tamper with the chain
    blockchain.chain[1].transactions[0].amount = 2.0
    assert blockchain.is_chain_valid() is False

def test_block_serialization(blockchain):
    """Test block serialization to JSON."""
    block = blockchain.chain[0]
    block_dict = block.to_dict()
    
    # Verify all required fields are present
    assert 'index' in block_dict
    assert 'timestamp' in block_dict
    assert 'transactions' in block_dict
    assert 'previous_hash' in block_dict
    assert 'nonce' in block_dict
    assert 'hash' in block_dict

def test_transaction_serialization(wallets):
    """Test transaction serialization to JSON."""
    alice, bob = wallets
    transaction = Transaction(
        sender=alice.address,
        recipient=bob.address,
        amount=1.0
    )
    transaction.sign(alice.private_key)
    
    transaction_dict = transaction.to_dict()
    assert 'sender' in transaction_dict
    assert 'recipient' in transaction_dict
    assert 'amount' in transaction_dict
    assert 'timestamp' in transaction_dict
    assert 'signature' in transaction_dict

def test_invalid_transaction_handling(blockchain, wallets):
    """Test handling of invalid transactions."""
    alice, bob = wallets
    
    # Create transaction without signature
    transaction = Transaction(
        sender=alice.address,
        recipient=bob.address,
        amount=1.0
    )
    
    # Attempt to add invalid transaction
    with pytest.raises(ValueError):
        blockchain.add_transaction(transaction)

def test_concurrent_transactions(blockchain, wallets):
    """Test handling multiple transactions."""
    alice, bob = wallets
    transactions = []
    
    # Create multiple transactions
    for i in range(5):
        transaction = Transaction(
            sender=alice.address,
            recipient=bob.address,
            amount=1.0
        )
        transaction.sign(alice.private_key)
        transactions.append(transaction)
    
    # Add all transactions
    for transaction in transactions:
        blockchain.add_transaction(transaction)
    
    # Mine block
    block = blockchain.mine_pending_transactions()
    
    # Verify all transactions were included
    assert len(block.transactions) == 5
    assert len(blockchain.pending_transactions) == 0

if __name__ == '__main__':
    pytest.main(['-v', 'test.py']) 