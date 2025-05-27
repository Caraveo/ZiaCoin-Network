import os
import sys
import shutil
import tempfile
import pytest

# Add the project root to sys.path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.wallet.wallet import WalletManager

def test_wallet_creation_and_recovery():
    # Use a temporary directory for wallet storage
    temp_dir = tempfile.mkdtemp()
    try:
        manager = WalletManager(storage_path=temp_dir)
        name = "testuser"
        passphrase = "testpassphrase"
        # Create wallet
        wallet = manager.create_wallet(name, passphrase)
        assert wallet.name == name
        assert wallet.address in manager.wallets
        # Load wallet
        loaded_wallet = manager.load_wallet(wallet.address, passphrase)
        assert loaded_wallet.address == wallet.address
        assert loaded_wallet.public_key == wallet.public_key
        # Recover wallet
        recovered_wallet = manager.recover_wallet(wallet.mnemonic, passphrase)
        assert recovered_wallet.address == wallet.address
        assert recovered_wallet.public_key == wallet.public_key
    finally:
        shutil.rmtree(temp_dir)

def test_wallet_index_file():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = WalletManager(storage_path=temp_dir)
        name = "indexuser"
        passphrase = "indexpass"
        wallet = manager.create_wallet(name, passphrase)
        index_path = os.path.join(temp_dir, "index.json")
        assert os.path.exists(index_path)
        with open(index_path, 'r') as f:
            data = f.read()
            assert name in data
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    pytest.main([__file__]) 