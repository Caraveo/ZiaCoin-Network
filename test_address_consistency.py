#!/usr/bin/env python3
"""
Test Address Consistency
This script demonstrates that wallet recovery produces the same address
"""

import sys
import os

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.wallet.wallet import Wallet, WalletManager
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

def test_address_consistency():
    """Test that wallet recovery produces the same address."""
    
    print("🔍 Testing Address Consistency")
    print("=" * 50)
    print()
    
    # Test mnemonic and passphrase
    test_mnemonic = "security elegant diet guard syrup express smooth there tone involve method danger"
    test_passphrase = "Roselawn$104-Founder-Wallet-2024"
    
    print_info("Test Parameters:")
    print(f"   Mnemonic: {test_mnemonic}")
    print(f"   Passphrase: {test_passphrase}")
    print()
    
    try:
        # Method 1: Direct wallet creation from mnemonic
        print_info("Method 1: Direct wallet creation from mnemonic...")
        wallet1 = Wallet.from_mnemonic(test_mnemonic, test_passphrase)
        print_success(f"Address 1: {wallet1.address}")
        print()
        
        # Method 2: Wallet recovery through WalletManager
        print_info("Method 2: Wallet recovery through WalletManager...")
        wallet_manager = WalletManager()
        wallet2 = wallet_manager.recover_wallet(test_mnemonic, test_passphrase)
        print_success(f"Address 2: {wallet2.address}")
        print()
        
        # Method 3: Create wallet again (should be same)
        print_info("Method 3: Create wallet again from same mnemonic...")
        wallet3 = Wallet.from_mnemonic(test_mnemonic, test_passphrase)
        print_success(f"Address 3: {wallet3.address}")
        print()
        
        # Compare addresses
        print("🔍 Address Comparison:")
        print(f"   Address 1: {wallet1.address}")
        print(f"   Address 2: {wallet2.address}")
        print(f"   Address 3: {wallet3.address}")
        print()
        
        # Check if all addresses are identical
        addresses = [wallet1.address, wallet2.address, wallet3.address]
        if len(set(addresses)) == 1:
            print_success("✅ ALL ADDRESSES ARE IDENTICAL!")
            print_info("   This proves wallet recovery is deterministic")
            print_info("   Same mnemonic + same passphrase = same address")
        else:
            print_error("❌ ADDRESSES ARE DIFFERENT!")
            print_error("   This would indicate a problem with wallet recovery")
            return False
        
        # Test with different passphrase
        print()
        print_info("Testing with different passphrase...")
        different_passphrase = "Different-Passphrase-123"
        wallet_diff = Wallet.from_mnemonic(test_mnemonic, different_passphrase)
        print_success(f"Address with different passphrase: {wallet_diff.address}")
        
        if wallet_diff.address != wallet1.address:
            print_success("✅ Different passphrase = Different address (correct!)")
        else:
            print_error("❌ Different passphrase should produce different address")
        
        print()
        print("🎉 Address consistency test completed successfully!")
        print("   Your wallet recovery system is working correctly")
        print("   Recovered wallets will have the SAME address as the original")
        
        return True
        
    except Exception as e:
        print_error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_address_consistency() 