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
        """Initialize the wallet manager with explicit path handling."""
        # Ensure storage_path is absolute and exists
        self.storage_path = os.path.abspath(storage_path)
        print_info(f"[DEBUG] Initializing WalletManager with storage_path: {self.storage_path}")
        
        # Create storage directory if it doesn't exist
        try:
            os.makedirs(self.storage_path, exist_ok=True)
        except Exception as e:
            print_error(f"Failed to create storage directory: {e}")
            raise
        
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
        self.storage = ChainStorage()
        
        # Initialize encryption with the correct key file path
        key_file = "chain/keys/master.key"  # Use the same key file as the rest of the system
        self.encryption = Encryption(key_file=key_file)
        
        self.initialize()

    def initialize(self) -> bool:
        """Initialize the wallet manager."""
        try:
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
            index_path = os.path.join(self.storage_path, "index.json")
            print_info(f"[DEBUG] Saving wallet index to: {index_path}")
            
            with open(index_path, 'w') as f:
                json.dump({
                    "wallets": self.wallets,
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
            print_info(f"[DEBUG] Loading wallets from: {self.storage_path}")
            index_path = os.path.join(self.storage_path, "index.json")
            print_info(f"[DEBUG] Looking for index file: {index_path}")
            
            if os.path.exists(index_path):
                print_info("[DEBUG] Index file found, loading wallets...")
                with open(index_path, 'r') as f:
                    index = json.load(f)
                    self.wallets = index.get("wallets", {})
                print_success(f"Loaded {len(self.wallets)} wallets")
                
                # List the loaded wallets
                for address, info in self.wallets.items():
                    print_info(f"  - {info.get('name', 'Unknown')}: {address}")
            else:
                # Initialize empty wallet list if no index exists
                print_warning("[DEBUG] No wallet index found")
                self.wallets = {}
                print_info("No wallet index found, starting with empty wallet list")
        except Exception as e:
            print_error(f"Failed to load wallets: {e}")
            import traceback
            print_error(f"Traceback: {traceback.format_exc()}")
            # Initialize empty wallet list on error
            self.wallets = {}

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
                for address, info in index.get("wallets", {}).items():
                    # Handle both regular and recovered wallets
                    if info.get('type') == 'recovered':
                        # Recovered wallet - use full path
                        wallet_path = info['wallet_file']
                    else:
                        # Regular wallet - construct path
                        wallet_path = os.path.join(self.storage_path, info['wallet_file'])
                    
                    if not os.path.exists(wallet_path):
                        print_warning(f"Wallet file not found: {wallet_path}")
                        return False
                    
                    # Verify wallet data can be read (but don't decrypt without passphrase)
                    try:
                        with open(wallet_path, 'r') as wf:
                            encrypted_data = json.load(wf)
                            # Basic structure validation
                            if not isinstance(encrypted_data, dict):
                                print_warning(f"Invalid wallet file format: {wallet_path}")
                                return False
                            if 'encrypted_data' not in encrypted_data and 'salt' not in encrypted_data:
                                print_warning(f"Invalid wallet encryption format: {wallet_path}")
                                return False
                    except Exception as e:
                        print_warning(f"Failed to read wallet file {wallet_path}: {e}")
                        return False
            return True
        except Exception as e:
            print_error(f"Storage verification failed: {e}")
            return False

    def _verify_wallet_data(self, wallet_data: Dict) -> bool:
        """Verify the integrity of wallet data."""
        required_fields = ['address', 'public_key', 'private_key', 'name']
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
            # Create the wallet
            wallet = Wallet.create(name, passphrase)
            print_info(f"[DEBUG] Created wallet with address: {wallet.address}")
            
            # Prepare wallet data
            wallet_data = {
                'name': wallet.name,
                'address': wallet.address,
                'public_key': wallet.public_key,
                'private_key': wallet.private_key,
                'mnemonic': wallet.mnemonic,
                'created_at': time.time()
            }
            
            # Encrypt wallet data using password-based encryption
            encrypted_data = self.encryption.encrypt_with_password(
                json.dumps(wallet_data),
                passphrase
            )
            
            # Prepare file paths
            wallet_filename = f"{name}.wallet"
            wallet_path = os.path.join(self.storage_path, wallet_filename)
            
            print_info(f"[DEBUG] Saving wallet to: {wallet_path}")
            
            # Save encrypted wallet file
            try:
                with open(wallet_path, 'w') as f:
                    json.dump(encrypted_data, f)
                print_success(f"Wallet file saved: {wallet_filename}")
            except Exception as e:
                print_error(f"Failed to save wallet file: {e}")
                raise
            
            # Update wallet index
            self.wallets[wallet.address] = {
                'name': wallet.name,
                'address': wallet.address,
                'public_key': wallet.public_key,
                'wallet_file': wallet_filename
            }
            
            # Save wallet index
            try:
                self.save_state()
                print_success("Wallet index updated")
            except Exception as e:
                print_error(f"Failed to save wallet index: {e}")
                raise
            
            return wallet
            
        except Exception as e:
            print_error(f"Failed to create wallet: {e}")
            raise

    def load_wallet(self, address: str, passphrase: str) -> Wallet:
        """Load a wallet using its address and passphrase."""
        try:
            # Find wallet file from index
            wallet_info = self.wallets.get(address)
            if not wallet_info:
                raise ValueError("Wallet not found")
            
            # Handle both regular and recovered wallets
            if wallet_info.get('type') == 'recovered':
                # Recovered wallet - use full path
                wallet_path = wallet_info['wallet_file']
            else:
                # Regular wallet - construct path
                wallet_path = os.path.join(self.storage_path, wallet_info['wallet_file'])
            
            if not os.path.exists(wallet_path):
                raise ValueError("Wallet file not found")
            
            # Read and decrypt wallet data
            with open(wallet_path, 'r') as f:
                encrypted_data = json.load(f)
            
            # Decrypt using password-based decryption
            decrypted_data = self.encryption.decrypt_with_password(encrypted_data, passphrase)
            wallet_data = json.loads(decrypted_data)
            
            return Wallet(
                private_key=wallet_data['private_key'],
                public_key=wallet_data['public_key'],
                address=wallet_data['address'],
                mnemonic=wallet_data['mnemonic'],
                name=wallet_data['name']
            )
        except Exception as e:
            print_error(f"Failed to load wallet: {e}")
            raise ValueError("Invalid passphrase or corrupted wallet file")

    def recover_wallet(self, mnemonic_phrase: str, passphrase: str) -> Wallet:
        """Recover a wallet using its mnemonic phrase and passphrase."""
        try:
            # Step 1: Validate mnemonic phrase first (before creating anything)
            print_info("Validating mnemonic phrase...")
            mnemonic = Mnemonic()
            if not mnemonic.validate(mnemonic_phrase):
                raise ValueError("Invalid mnemonic phrase")
            
            # Step 2: Test wallet creation from mnemonic (validation only)
            print_info("Testing wallet derivation from mnemonic...")
            test_wallet = Wallet.from_mnemonic(mnemonic_phrase, passphrase)
            
            # Step 3: Prepare directory structure
            print_info("Preparing storage directory...")
            restored_dir = os.path.join("chain", "restored")
            os.makedirs(restored_dir, exist_ok=True)
            
            # Step 4: Check if wallet already exists
            existing_wallet_info = self.wallets.get(test_wallet.address)
            if existing_wallet_info:
                print_warning(f"Wallet with address {test_wallet.address} already exists")
                print_info("Loading existing wallet instead of creating new one")
                return self.load_wallet(test_wallet.address, passphrase)
            
            # Step 5: Prepare wallet data
            print_info("Preparing wallet data...")
            wallet_data = {
                'name': f"Recovered_{test_wallet.address[:8]}",
                'address': test_wallet.address,
                'public_key': test_wallet.public_key,
                'private_key': test_wallet.private_key,
                'mnemonic': test_wallet.mnemonic,
                'created_at': time.time()
            }
            
            # Step 6: Test encryption (before saving)
            print_info("Testing encryption...")
            encrypted_data = self.encryption.encrypt_with_password(
                json.dumps(wallet_data),
                passphrase
            )
            
            # Step 7: Prepare file path
            wallet_file = f"Recovered_{test_wallet.address[:8]}.wallet"
            wallet_path = os.path.join(restored_dir, wallet_file)
            
            # Step 8: Save wallet file (atomic operation)
            print_info("Saving recovered wallet...")
            try:
                with open(wallet_path, 'w') as f:
                    json.dump(encrypted_data, f)
                print_success(f"Recovered wallet saved: {wallet_path}")
            except Exception as e:
                print_error(f"Failed to save recovered wallet: {e}")
                # Clean up any partial files
                if os.path.exists(wallet_path):
                    os.remove(wallet_path)
                raise
            
            # Step 9: Update wallet index (only after successful save)
            print_info("Updating wallet index...")
            self.wallets[test_wallet.address] = {
                'name': wallet_data['name'],
                'address': test_wallet.address,
                'public_key': test_wallet.public_key,
                'wallet_file': wallet_path,  # Store full path for recovered wallets
                'type': 'recovered',
                'restored_at': time.time()
            }
            
            # Step 10: Save wallet index
            try:
                self.save_state()
                print_success("Wallet index updated successfully")
            except Exception as e:
                print_error(f"Failed to save wallet index: {e}")
                # Clean up wallet file if index save fails
                if os.path.exists(wallet_path):
                    os.remove(wallet_path)
                raise
            
            print_success("✅ Wallet recovery completed successfully!")
            return test_wallet
            
        except Exception as e:
            print_error(f"❌ Wallet recovery failed: {e}")
            # Ensure no partial data is left behind
            if 'test_wallet' in locals() and 'wallet_path' in locals():
                if os.path.exists(wallet_path):
                    os.remove(wallet_path)
            raise

    def list_wallets(self):
        """List all wallets (public info only)."""
        return [info for info in self.wallets.values()]

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