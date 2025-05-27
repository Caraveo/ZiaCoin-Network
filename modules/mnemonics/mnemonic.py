import hashlib
import hmac
import os
from typing import List, Optional
import csv
from pathlib import Path

class Mnemonic:
    def __init__(self):
        self.wordlist = self._load_wordlist()
        self.entropy_bits = 128  # 12 words
        self.checksum_bits = 4   # 1/32 of entropy
        self.total_bits = self.entropy_bits + self.checksum_bits
        self.word_count = 12     # Number of words in the mnemonic

    def _load_wordlist(self) -> List[str]:
        """Load the BIP39 wordlist from CSV."""
        wordlist_path = Path(__file__).parent / 'word.csv'
        with open(wordlist_path, 'r') as f:
            reader = csv.reader(f)
            # The CSV has a single row with all words
            words = next(reader)
            # Clean up the words (remove quotes and whitespace)
            return [word.strip().strip('"') for word in words]

    def _generate_entropy(self) -> bytes:
        """Generate cryptographically secure random entropy."""
        return os.urandom(self.entropy_bits // 8)

    def _entropy_to_mnemonic(self, entropy: bytes) -> str:
        """Convert entropy to mnemonic phrase."""
        # Calculate checksum
        checksum = hashlib.sha256(entropy).digest()[0]
        checksum_bits = bin(checksum)[2:].zfill(8)[:self.checksum_bits]
        
        # Combine entropy and checksum
        entropy_bits = ''.join(bin(b)[2:].zfill(8) for b in entropy)
        combined_bits = entropy_bits + checksum_bits
        
        # Convert bits to words
        words = []
        for i in range(0, len(combined_bits), 11):
            index = int(combined_bits[i:i+11], 2)
            words.append(self.wordlist[index])
        
        return ' '.join(words)

    def _mnemonic_to_entropy(self, mnemonic: str) -> bytes:
        """Convert mnemonic phrase back to entropy."""
        words = mnemonic.split()
        if len(words) != self.word_count:
            raise ValueError(f"Invalid mnemonic length. Expected {self.word_count} words.")

        # Convert words to bits
        word_to_index = {word: i for i, word in enumerate(self.wordlist)}
        combined_bits = ''
        for word in words:
            if word not in word_to_index:
                raise ValueError(f"Invalid word in mnemonic: {word}")
            index = word_to_index[word]
            combined_bits += bin(index)[2:].zfill(11)

        # Split entropy and checksum
        entropy_bits = combined_bits[:-self.checksum_bits]
        checksum_bits = combined_bits[-self.checksum_bits:]

        # Convert entropy bits to bytes
        entropy_bytes = bytes(int(entropy_bits[i:i+8], 2) for i in range(0, len(entropy_bits), 8))

        # Verify checksum
        checksum = hashlib.sha256(entropy_bytes).digest()[0]
        expected_checksum = bin(checksum)[2:].zfill(8)[:self.checksum_bits]
        if checksum_bits != expected_checksum:
            raise ValueError("Invalid mnemonic checksum")

        return entropy_bytes

    def generate(self) -> str:
        """Generate a new mnemonic phrase."""
        entropy = self._generate_entropy()
        return self._entropy_to_mnemonic(entropy)

    def validate(self, mnemonic: str) -> bool:
        """Validate a mnemonic phrase."""
        try:
            self._mnemonic_to_entropy(mnemonic)
            return True
        except ValueError:
            return False

    def to_seed(self, mnemonic: str, passphrase: str = "") -> bytes:
        """Convert mnemonic to seed using PBKDF2."""
        if not self.validate(mnemonic):
            raise ValueError("Invalid mnemonic phrase")

        # Normalize inputs
        mnemonic_bytes = mnemonic.encode('utf-8')
        passphrase_bytes = passphrase.encode('utf-8')
        
        # Use PBKDF2 to derive the seed
        seed = hashlib.pbkdf2_hmac(
            'sha512',
            mnemonic_bytes,
            b'mnemonic' + passphrase_bytes,
            2048  # Number of iterations
        )
        
        return seed

    def to_hex(self, mnemonic: str) -> str:
        """Convert mnemonic to hex string."""
        entropy = self._mnemonic_to_entropy(mnemonic)
        return entropy.hex()

    @staticmethod
    def from_hex(hex_string: str) -> str:
        """Convert hex string to mnemonic."""
        if len(hex_string) != 32:  # 16 bytes = 128 bits
            raise ValueError("Invalid hex string length")
        
        try:
            entropy = bytes.fromhex(hex_string)
            mnemonic = Mnemonic()
            return mnemonic._entropy_to_mnemonic(entropy)
        except ValueError:
            raise ValueError("Invalid hex string")

def main():
    # Example usage
    mnemonic = Mnemonic()
    
    # Generate new mnemonic
    phrase = mnemonic.generate()
    print(f"Generated mnemonic: {phrase}")
    
    # Validate mnemonic
    is_valid = mnemonic.validate(phrase)
    print(f"Is valid: {is_valid}")
    
    # Convert to seed
    seed = mnemonic.to_seed(phrase)
    print(f"Seed (hex): {seed.hex()}")
    
    # Convert to hex
    hex_string = mnemonic.to_hex(phrase)
    print(f"Hex: {hex_string}")
    
    # Convert back from hex
    recovered_phrase = Mnemonic.from_hex(hex_string)
    print(f"Recovered phrase: {recovered_phrase}")
    print(f"Matches original: {phrase == recovered_phrase}")

if __name__ == "__main__":
    main() 