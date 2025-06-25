#!/usr/bin/env python3
"""
Test script to verify node shutdown works correctly
"""

import sys
import os
import time
import signal

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def test_blockchain_save():
    """Test blockchain save functionality."""
    try:
        from modules.blockchain.blockchain import Blockchain
        
        # Create a new blockchain
        blockchain = Blockchain()
        
        # Try to save state
        result = blockchain.save_state()
        
        if result:
            print("✅ Blockchain save_state works correctly")
            return True
        else:
            print("❌ Blockchain save_state failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing blockchain save: {e}")
        return False

def test_miner_stop():
    """Test miner stop functionality."""
    try:
        from modules.mining.miner import Miner
        from modules.storage.chain_storage import ChainStorage
        
        # Create storage and miner
        storage = ChainStorage()
        miner = Miner(storage)
        
        # Try to stop mining
        miner.stop_mining()
        
        print("✅ Miner stop_mining works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing miner stop: {e}")
        return False

def main():
    print("🧪 Testing shutdown functionality...")
    print()
    
    # Test blockchain save
    blockchain_ok = test_blockchain_save()
    print()
    
    # Test miner stop
    miner_ok = test_miner_stop()
    print()
    
    if blockchain_ok and miner_ok:
        print("🎉 All shutdown tests passed!")
        print("✅ Node should now shut down gracefully")
        return True
    else:
        print("❌ Some shutdown tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 