import secrets
import hashlib
import base58
from typing import Tuple, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from modules.mnemonics.mnemonic import Mnemonic

@dataclass
class Wallet:
    private_key: str
    public_key: str
    address: str
    mnemonic: Optional[str] = None

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
                encoding=ec.Encoding.X962,
                format=ec.PublicFormat.CompressedPoint
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
    def create(cls) -> 'Wallet':
        """Create a new wallet instance with generated keys and address."""
        # Generate mnemonic
        mnemonic = Mnemonic()
        mnemonic_phrase = mnemonic.generate()
        
        # Use mnemonic to generate seed
        seed = mnemonic.to_seed(mnemonic_phrase)
        
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

    @classmethod
    def from_mnemonic(cls, mnemonic_phrase: str) -> 'Wallet':
        """Create a wallet from a mnemonic phrase."""
        mnemonic = Mnemonic()
        if not mnemonic.validate(mnemonic_phrase):
            raise ValueError("Invalid mnemonic phrase")
        
        # Generate seed from mnemonic
        seed = mnemonic.to_seed(mnemonic_phrase)
        
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
        return f"Wallet Address: {self.address}\nPublic Key: {self.public_key}\nPrivate Key: {self.private_key}\nMnemonic: {self.mnemonic}"

def main():
    try:
        # Create a new wallet
        wallet = Wallet.create()
        print("\nNew Wallet:")
        print(wallet)
        
        # Recover wallet from mnemonic
        recovered_wallet = Wallet.from_mnemonic(wallet.mnemonic)
        print("\nRecovered Wallet:")
        print(recovered_wallet)
        
        # Verify recovery
        print(f"\nRecovery successful: {wallet.address == recovered_wallet.address}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()