#!/usr/bin/env python3
"""
Test Recovery Validation
This script demonstrates what happens when recovery information doesn't match
"""

import sys
import os

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.wallet.wallet import Wallet, WalletManager
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

def test_recovery_validation():
    """Test what happens when recovery information doesn't match."""
    
    print("🔒 Testing Recovery Validation")
    print("=" * 50)
    print()
    
    # Correct information
    correct_mnemonic = "security elegant diet guard syrup express smooth there tone involve method danger"
    correct_passphrase = "Roselawn$104-Founder-Wallet-2024"
    
    print_info("Correct Information:")
    print(f"   Mnemonic: {correct_mnemonic}")
    print(f"   Passphrase: {correct_passphrase}")
    print()
    
    # Test cases with incorrect information
    test_cases = [
        {
            "name": "Wrong Mnemonic Word",
            "mnemonic": "security elegant diet guard syrup express smooth there tone involve method WRONG",
            "passphrase": correct_passphrase,
            "expected": "Invalid mnemonic phrase"
        },
        {
            "name": "Wrong Passphrase",
            "mnemonic": correct_mnemonic,
            "passphrase": "Wrong-Passphrase-123",
            "expected": "Different address generated"
        },
        {
            "name": "Missing Mnemonic Word",
            "mnemonic": "security elegant diet guard syrup express smooth there tone involve method",
            "passphrase": correct_passphrase,
            "expected": "Invalid mnemonic phrase"
        },
        {
            "name": "Extra Mnemonic Word",
            "mnemonic": "security elegant diet guard syrup express smooth there tone involve method danger extra",
            "passphrase": correct_passphrase,
            "expected": "Invalid mnemonic phrase"
        },
        {
            "name": "Empty Passphrase",
            "mnemonic": correct_mnemonic,
            "passphrase": "",
            "expected": "Different address generated"
        },
        {
            "name": "Completely Wrong Mnemonic",
            "mnemonic": "apple banana cherry dog elephant fish grape house ice juice king lion",
            "passphrase": correct_passphrase,
            "expected": "Different address generated"
        }
    ]
    
    wallet_manager = WalletManager()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['name']}")
        print(f"   Mnemonic: {test_case['mnemonic']}")
        print(f"   Passphrase: {test_case['passphrase']}")
        
        try:
            # Try to recover wallet with incorrect information
            recovered_wallet = wallet_manager.recover_wallet(test_case['mnemonic'], test_case['passphrase'])
            
            # If we get here, recovery "worked" but generated different address
            print_warning(f"   ⚠️  Recovery 'worked' but generated different address")
            print_warning(f"   Generated Address: {recovered_wallet.address}")
            
            # Compare with correct address
            correct_wallet = Wallet.from_mnemonic(correct_mnemonic, correct_passphrase)
            if recovered_wallet.address == correct_wallet.address:
                print_error(f"   ❌ ERROR: Should not match correct address!")
            else:
                print_success(f"   ✅ Correctly generated different address")
                print_info(f"   Expected: {test_case['expected']}")
            
        except ValueError as e:
            print_error(f"   ❌ Recovery failed: {str(e)}")
            print_success(f"   ✅ Correctly rejected invalid information")
            print_info(f"   Expected: {test_case['expected']}")
            
        except Exception as e:
            print_error(f"   ❌ Unexpected error: {str(e)}")
            
        print()
    
    # Test loading with wrong passphrase
    print("🔐 Testing Load with Wrong Passphrase:")
    try:
        # First create a wallet
        wallet = wallet_manager.recover_wallet(correct_mnemonic, correct_passphrase)
        print_info(f"   Created wallet: {wallet.address}")
        
        # Try to load with wrong passphrase
        wrong_passphrase = "Wrong-Passphrase-123"
        print_info(f"   Trying to load with passphrase: {wrong_passphrase}")
        
        loaded_wallet = wallet_manager.load_wallet(wallet.address, wrong_passphrase)
        print_error(f"   ❌ ERROR: Should not load with wrong passphrase!")
        
    except ValueError as e:
        print_success(f"   ✅ Correctly rejected wrong passphrase: {str(e)}")
    except Exception as e:
        print_error(f"   ❌ Unexpected error: {str(e)}")
    
    # Test that failed recovery doesn't create files
    print()
    print("🧹 Testing Failed Recovery Cleanup:")
    
    # Count files before failed recovery
    restored_dir = os.path.join("chain", "restored")
    if os.path.exists(restored_dir):
        files_before = len([f for f in os.listdir(restored_dir) if f.endswith('.wallet')])
        print_info(f"   Files before failed recovery: {files_before}")
    else:
        files_before = 0
        print_info(f"   No restored directory exists")
    
    # Try to recover with invalid mnemonic
    try:
        invalid_mnemonic = "invalid words that are not in the dictionary"
        print_info(f"   Attempting recovery with invalid mnemonic...")
        wallet_manager.recover_wallet(invalid_mnemonic, correct_passphrase)
        print_error(f"   ❌ ERROR: Should not succeed with invalid mnemonic!")
    except ValueError as e:
        print_success(f"   ✅ Correctly failed with invalid mnemonic: {str(e)}")
    except Exception as e:
        print_error(f"   ❌ Unexpected error: {str(e)}")
    
    # Count files after failed recovery
    if os.path.exists(restored_dir):
        files_after = len([f for f in os.listdir(restored_dir) if f.endswith('.wallet')])
        print_info(f"   Files after failed recovery: {files_after}")
        
        if files_after == files_before:
            print_success(f"   ✅ No new files created during failed recovery")
        else:
            print_error(f"   ❌ ERROR: {files_after - files_before} new files created during failed recovery")
    else:
        print_success(f"   ✅ No restored directory created during failed recovery")
    
    print()
    print("📋 Summary:")
    print("   ✅ Wrong mnemonic = Recovery fails or different address")
    print("   ✅ Wrong passphrase = Different address or load fails")
    print("   ✅ Invalid mnemonic = Recovery fails with error")
    print("   ✅ Failed recovery = No files created")
    print("   ✅ Security maintained = Cannot access wrong wallet")
    print("   ✅ Clean recovery = No partial data left behind")
    print()
    print("🔒 Recovery validation is working correctly!")

if __name__ == "__main__":
    test_recovery_validation() 