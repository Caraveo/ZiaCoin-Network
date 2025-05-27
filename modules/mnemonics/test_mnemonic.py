import pytest
from .mnemonic import Mnemonic

@pytest.fixture
def mnemonic():
    return Mnemonic()

def test_mnemonic_generation(mnemonic):
    """Test mnemonic phrase generation."""
    phrase = mnemonic.generate()
    words = phrase.split()
    
    # Check length
    assert len(words) == 12
    
    # Check all words are in wordlist
    for word in words:
        assert word in mnemonic.wordlist

def test_mnemonic_validation(mnemonic):
    """Test mnemonic phrase validation."""
    # Valid mnemonic
    valid_phrase = mnemonic.generate()
    assert mnemonic.validate(valid_phrase) is True
    
    # Invalid length
    invalid_phrase = " ".join(valid_phrase.split()[:11])
    assert mnemonic.validate(invalid_phrase) is False
    
    # Invalid word
    words = valid_phrase.split()
    words[0] = "invalidword"
    invalid_phrase = " ".join(words)
    assert mnemonic.validate(invalid_phrase) is False

def test_mnemonic_to_seed(mnemonic):
    """Test mnemonic to seed conversion."""
    phrase = mnemonic.generate()
    seed = mnemonic.to_seed(phrase)
    
    # Check seed length (512 bits = 64 bytes)
    assert len(seed) == 64
    
    # Test with passphrase
    passphrase = "test passphrase"
    seed_with_passphrase = mnemonic.to_seed(phrase, passphrase)
    assert seed != seed_with_passphrase

def test_mnemonic_to_hex(mnemonic):
    """Test mnemonic to hex conversion."""
    phrase = mnemonic.generate()
    hex_string = mnemonic.to_hex(phrase)
    
    # Check hex string length (32 bytes = 64 hex characters)
    assert len(hex_string) == 64
    
    # Test conversion back to mnemonic
    recovered_phrase = Mnemonic.from_hex(hex_string)
    assert phrase == recovered_phrase

def test_invalid_hex_conversion():
    """Test invalid hex string handling."""
    with pytest.raises(ValueError):
        Mnemonic.from_hex("invalid")
    
    with pytest.raises(ValueError):
        Mnemonic.from_hex("00" * 16)  # Too short

def test_mnemonic_recovery(mnemonic):
    """Test mnemonic recovery process."""
    # Generate original mnemonic
    original_phrase = mnemonic.generate()
    original_seed = mnemonic.to_seed(original_phrase)
    
    # Convert to hex and back
    hex_string = mnemonic.to_hex(original_phrase)
    recovered_phrase = Mnemonic.from_hex(hex_string)
    recovered_seed = mnemonic.to_seed(recovered_phrase)
    
    # Verify recovery
    assert original_phrase == recovered_phrase
    assert original_seed == recovered_seed

def test_mnemonic_checksum(mnemonic):
    """Test mnemonic checksum validation."""
    phrase = mnemonic.generate()
    
    # Tamper with the phrase
    words = phrase.split()
    words[-1] = mnemonic.wordlist[0]  # Replace last word
    tampered_phrase = " ".join(words)
    
    # Verify checksum fails
    assert mnemonic.validate(tampered_phrase) is False

if __name__ == "__main__":
    pytest.main(['-v', 'test_mnemonic.py']) 