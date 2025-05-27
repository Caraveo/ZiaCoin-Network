#!/usr/bin/env python3
import sys
import os
import json
import time
import shutil
from typing import Dict

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import the sync module
from modules.sync.sync import CodeSync
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

def check_sync():
    """Check if code is synchronized with remote repository."""
    sync = CodeSync()
    if not sync.sync():
        print("Code synchronization failed. Please update your code.")
        sys.exit(1)

# Check code synchronization before proceeding
check_sync()

import secrets
import hashlib
import base58
import argparse
from typing import Tuple, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from modules.mnemonics.mnemonic import Mnemonic
from modules.storage import ChainStorage
from modules.encryption import Encryption

@dataclass
class Wallet:
    private_key: str
    public_key: str
    address: str
    mnemonic: Optional[str] = None
    name: Optional[str] = None

    @staticmethod
    def generate_private_key() -> str:
        """Generate a secure private key using cryptographic randomness."""
        return secrets.token_hex(32)

    @staticmethod
    def generate_public_key(private_key: str) -> str:
        """Generate a public key from a private key using secp256k1."""
        try:
            private_key_bytes = bytes.fromhex(private_key)
            private_key_obj = ec.derive_private_key(
                int.from_bytes(private_key_bytes, 'big'),
                ec.SECP256K1(),
                default_backend()
            )
            public_key_obj = private_key_obj.public_key()
            public_key_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.CompressedPoint
            )
            return public_key_bytes.hex()
        except Exception as e:
            raise ValueError(f"Failed to generate public key: {str(e)}")

    @staticmethod
    def generate_address(public_key: str) -> str:
        """Generate a wallet address from a public key."""
        try:
            public_key_bytes = bytes.fromhex(public_key)
            sha256_hash = hashlib.sha256(public_key_bytes).digest()
            ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
            version = b'\x00'  # Main network version
            vh160 = version + ripemd160_hash
            checksum = hashlib.sha256(hashlib.sha256(vh160).digest()).digest()[:4]
            binary_address = vh160 + checksum
            return base58.b58encode(binary_address).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to generate address: {str(e)}")

    @classmethod
    def create(cls, name: str, passphrase: str) -> 'Wallet':
        """Create a new wallet instance with generated keys and address."""
        try:
            # Generate mnemonic
            mnemonic = Mnemonic()
            mnemonic_phrase = mnemonic.generate()
            
            # Use mnemonic and passphrase to generate seed
            seed = mnemonic.to_seed(mnemonic_phrase, passphrase)
            
            # Use first 32 bytes of seed as private key
            private_key = seed[:32].hex()
            public_key = cls.generate_public_key(private_key)
            address = cls.generate_address(public_key)
            
            return cls(
                private_key=private_key,
                public_key=public_key,
                address=address,
                mnemonic=mnemonic_phrase,
                name=name
            )
        except Exception as e:
            raise ValueError(f"Failed to create wallet: {str(e)}")

    @classmethod
    def from_mnemonic(cls, mnemonic_phrase: str, passphrase: str) -> 'Wallet':
        """Create a wallet from a mnemonic phrase and passphrase."""
        mnemonic = Mnemonic()
        if not mnemonic.validate(mnemonic_phrase):
            raise ValueError("Invalid mnemonic phrase")
        
        # Generate seed from mnemonic and passphrase
        seed = mnemonic.to_seed(mnemonic_phrase, passphrase)
        
        # Use first 32 bytes of seed as private key
        private_key = seed[:32].hex()
        public_key = cls.generate_public_key(private_key)
        address = cls.generate_address(public_key)
        
        return cls(
            private_key=private_key,
            public_key=public_key,
            address=address,
            mnemonic=mnemonic_phrase
        )

    def __str__(self) -> str:
        """Return a string representation of the wallet."""
        return f"Wallet Name: {self.name}\nAddress: {self.address}\nPublic Key: {self.public_key}\nMnemonic: {self.mnemonic}"

class WalletManager:
    def __init__(self, storage_path: str = "wallets/", encryption_config: Dict = None, mnemonic_config: Dict = None):
        self.storage_path = storage_path
        self.encryption_config = encryption_config or {
            "algorithm": "AES-GCM",
            "key_derivation": "PBKDF2",
            "iterations": 100000
        }
        self.mnemonic_config = mnemonic_config or {
            "word_count": 12,
            "language": "english"
        }
        self.wallets = {}
        self.storage = ChainStorage()  # Initialize storage
        self.initialize()

    def initialize(self) -> bool:
        """Initialize the wallet manager."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Load existing wallets
            self._load_wallets()
            
            print_success("Wallet manager initialized")
            return True
        except Exception as e:
            print_error(f"Failed to initialize wallet manager: {e}")
            return False

    def save_state(self) -> bool:
        """Save the current state of all wallets."""
        try:
            # Save each wallet
            for address, wallet in self.wallets.items():
                wallet_path = os.path.join(self.storage_path, f"{address}.json")
                with open(wallet_path, 'w') as f:
                    json.dump(wallet.to_dict(), f, indent=4)
            
            # Save wallet index
            index_path = os.path.join(self.storage_path, "index.json")
            with open(index_path, 'w') as f:
                json.dump({
                    "wallets": list(self.wallets.keys()),
                    "timestamp": time.time()
                }, f, indent=4)
            
            print_success("Wallet state saved")
            return True
        except Exception as e:
            print_error(f"Failed to save wallet state: {e}")
            return False

    def _load_wallets(self) -> None:
        """Load all wallets from storage."""
        try:
            index_path = os.path.join(self.storage_path, "index.json")
            if os.path.exists(index_path):
                with open(index_path, 'r') as f:
                    index = json.load(f)
                    for address in index.get("wallets", []):
                        wallet_path = os.path.join(self.storage_path, f"{address}.json")
                        if os.path.exists(wallet_path):
                            with open(wallet_path, 'r') as wf:
                                wallet_data = json.load(wf)
                                self.wallets[address] = Wallet.from_dict(wallet_data)
                print_success(f"Loaded {len(self.wallets)} wallets")
        except Exception as e:
            print_error(f"Failed to load wallets: {e}")

    def verify_storage(self) -> bool:
        """Verify the integrity of wallet storage."""
        try:
            # Check storage directory
            if not os.path.exists(self.storage_path):
                print_warning("Wallet storage directory not found")
                return False
            
            # Check index file
            index_path = os.path.join(self.storage_path, "index.json")
            if not os.path.exists(index_path):
                print_warning("Wallet index not found")
                return False
            
            # Verify each wallet file
            with open(index_path, 'r') as f:
                index = json.load(f)
                for address in index.get("wallets", []):
                    wallet_path = os.path.join(self.storage_path, f"{address}.json")
                    if not os.path.exists(wallet_path):
                        print_warning(f"Wallet file not found: {address}")
                        return False
                    
                    # Verify wallet data
                    with open(wallet_path, 'r') as wf:
                        wallet_data = json.load(wf)
                        if not self._verify_wallet_data(wallet_data):
                            print_warning(f"Invalid wallet data: {address}")
                            return False
            
            return True
        except Exception as e:
            print_error(f"Storage verification failed: {e}")
            return False

    def _verify_wallet_data(self, wallet_data: Dict) -> bool:
        """Verify the integrity of wallet data."""
        required_fields = ['address', 'public_key', 'encrypted_private_key']
        return all(field in wallet_data for field in required_fields)

    def recover_storage(self) -> bool:
        """Attempt to recover wallet storage from corruption."""
        try:
            # Create backup of current storage
            backup_path = f"{self.storage_path}.backup"
            if os.path.exists(self.storage_path):
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                shutil.copytree(self.storage_path, backup_path)
            
            # Recreate storage directory
            if os.path.exists(self.storage_path):
                shutil.rmtree(self.storage_path)
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Try to recover wallets from backup
            if os.path.exists(backup_path):
                for file in os.listdir(backup_path):
                    if file.endswith('.json'):
                        try:
                            with open(os.path.join(backup_path, file), 'r') as f:
                                wallet_data = json.load(f)
                                if self._verify_wallet_data(wallet_data):
                                    with open(os.path.join(self.storage_path, file), 'w') as wf:
                                        json.dump(wallet_data, wf, indent=4)
                        except Exception as e:
                            print_warning(f"Failed to recover wallet {file}: {e}")
            
            # Reload wallets
            self._load_wallets()
            return True
        except Exception as e:
            print_error(f"Storage recovery failed: {e}")
            return False

    def create_wallet(self, name: str, passphrase: str) -> Wallet:
        """Create a new wallet and save it securely."""
        try:
            wallet = Wallet.create(name, passphrase)
            
            # Save wallet data
            wallet_data = {
                'name': wallet.name,
                'address': wallet.address,
                'public_key': wallet.public_key,
                'private_key': wallet.private_key,
                'mnemonic': wallet.mnemonic
            }
            
            # Save to file
            wallet_path = os.path.join(self.storage_path, f"{wallet.address}.json")
            os.makedirs(os.path.dirname(wallet_path), exist_ok=True)
            
            with open(wallet_path, 'w') as f:
                json.dump(wallet_data, f, indent=4)
            
            # Update wallet index
            self.wallets[wallet.address] = wallet
            self.save_state()
            
            return wallet
        except Exception as e:
            print_error(f"Failed to create wallet: {e}")
            raise

    def load_wallet(self, address: str, passphrase: str) -> Wallet:
        """Load a wallet using its address and passphrase."""
        wallet_data = self.storage.load_wallet(address, password=passphrase)
        if not wallet_data:
            raise ValueError("Wallet not found or invalid passphrase")
        
        return Wallet(
            private_key=wallet_data['private_key'],
            public_key=wallet_data['public_key'],
            address=wallet_data['address'],
            mnemonic=wallet_data['mnemonic'],
            name=wallet_data['name']
        )

    def recover_wallet(self, mnemonic_phrase: str, passphrase: str) -> Wallet:
        """Recover a wallet using its mnemonic phrase and passphrase."""
        wallet = Wallet.from_mnemonic(mnemonic_phrase, passphrase)
        
        # Save recovered wallet
        wallet_data = {
            'name': f"Recovered_{wallet.address[:8]}",
            'address': wallet.address,
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'mnemonic': wallet.mnemonic
        }
        
        self.storage.save_wallet(wallet.address, wallet_data, password=passphrase)
        
        return wallet

def main():
    parser = argparse.ArgumentParser(description='ZiaCoin Wallet Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create wallet command
    create_parser = subparsers.add_parser('createrecord', help='Create a new wallet')
    create_parser.add_argument('name', help='Name for the wallet')
    create_parser.add_argument('passphrase', help='Passphrase for wallet encryption')

    # Load wallet command
    load_parser = subparsers.add_parser('load', help='Load an existing wallet')
    load_parser.add_argument('address', help='Wallet address')
    load_parser.add_argument('passphrase', help='Wallet passphrase')

    # Recover wallet command
    recover_parser = subparsers.add_parser('recover', help='Recover wallet from mnemonic')
    recover_parser.add_argument('mnemonic', help='Mnemonic phrase')
    recover_parser.add_argument('passphrase', help='Wallet passphrase')

    args = parser.parse_args()
    wallet_manager = WalletManager()

    try:
        if args.command == 'createrecord':
            wallet = wallet_manager.create_wallet(args.name, args.passphrase)
            print("\nNew Wallet Created:")
            print(wallet)
            print("\nIMPORTANT: Save your mnemonic phrase securely!")
            print("You will need it to recover your wallet if you lose access.")
            
        elif args.command == 'load':
            wallet = wallet_manager.load_wallet(args.address, args.passphrase)
            print("\nWallet Loaded:")
            print(wallet)
            
        elif args.command == 'recover':
            wallet = wallet_manager.recover_wallet(args.mnemonic, args.passphrase)
            print("\nWallet Recovered:")
            print(wallet)
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()