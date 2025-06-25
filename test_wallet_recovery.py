#!/usr/bin/env python3
"""
Test Wallet Recovery
This script tests the wallet recovery functionality
"""

import sys
import os

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.wallet.wallet import WalletManager
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

def test_wallet_recovery():
    """Test wallet recovery functionality."""
    
    print("🧪 Testing Wallet Recovery")
    print("=" * 40)
    print()
    
    try:
        # Initialize wallet manager
        print_info("Initializing wallet manager...")
        wallet_manager = WalletManager()
        
        # Test mnemonic and passphrase from genesis_wallets.json
        test_mnemonic = "security elegant diet guard syrup express smooth there tone involve method danger"
        test_passphrase = "Roselawn$104-Founder-Wallet-2024"
        
        print_info("Testing wallet recovery...")
        print_info(f"Mnemonic: {test_mnemonic}")
        print_info(f"Passphrase: {test_passphrase}")
        print()
        
        # Recover wallet
        recovered_wallet = wallet_manager.recover_wallet(test_mnemonic, test_passphrase)
        
        print_success("✅ Wallet recovered successfully!")
        print_info(f"Address: {recovered_wallet.address}")
        print_info(f"Public Key: {recovered_wallet.public_key}")
        print_info(f"Name: {recovered_wallet.name}")
        print()
        
        # Test loading the recovered wallet
        print_info("Testing wallet loading...")
        loaded_wallet = wallet_manager.load_wallet(recovered_wallet.address, test_passphrase)
        
        print_success("✅ Wallet loaded successfully!")
        print_info(f"Loaded Address: {loaded_wallet.address}")
        print_info(f"Loaded Public Key: {loaded_wallet.public_key}")
        print()
        
        # Verify addresses match
        if recovered_wallet.address == loaded_wallet.address:
            print_success("✅ Address verification passed!")
        else:
            print_error("❌ Address verification failed!")
            return False
        
        # List all wallets
        print_info("Listing all wallets:")
        wallets = wallet_manager.list_wallets()
        for i, wallet_info in enumerate(wallets):
            wallet_type = wallet_info.get('type', 'regular')
            print(f"   {i+1}. {wallet_info['name']}: {wallet_info['address']} ({wallet_type})")
        
        # Check if recovered wallet file exists in chain/restored
        restored_dir = os.path.join("chain", "restored")
        if os.path.exists(restored_dir):
            restored_files = [f for f in os.listdir(restored_dir) if f.endswith('.wallet')]
            print_info(f"Recovered wallets in {restored_dir}: {len(restored_files)}")
            for file in restored_files:
                print(f"   - {file}")
        else:
            print_warning(f"Restored directory not found: {restored_dir}")
        
        print()
        print("🎉 Wallet recovery test completed successfully!")
        print("   Recovered wallets are now stored in chain/restored/")
        return True
        
    except Exception as e:
        print_error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_wallet_recovery() 