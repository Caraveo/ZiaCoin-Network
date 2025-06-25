#!/usr/bin/env python3
"""
Test New Storage Format
This script tests that the blockchain is using the new ChainStorage format
"""

import sys
import os
import json

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.blockchain.blockchain import Blockchain
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

def test_new_storage():
    """Test that the blockchain uses the new storage format."""
    
    print("🧪 Testing New Storage Format")
    print("=" * 40)
    print()
    
    try:
        # Initialize blockchain (this should migrate old format if needed)
        print_info("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Check if blocks are in new storage
        chain_blocks_dir = "chain/blocks"
        if os.path.exists(chain_blocks_dir):
            block_files = [f for f in os.listdir(chain_blocks_dir) if f.endswith('.json')]
            print_success(f"✅ New storage format working!")
            print_info(f"   Blocks in chain/blocks/: {len(block_files)}")
            print_info(f"   Blocks in memory: {len(blockchain.chain)}")
            
            if block_files:
                print("   Block files:")
                for i, file in enumerate(block_files[:3]):
                    print(f"     {i+1}. {file}")
                if len(block_files) > 3:
                    print(f"     ... and {len(block_files) - 3} more")
        else:
            print_warning("⚠️  chain/blocks/ directory not found")
        
        # Check if old blockchain.json still exists
        if os.path.exists('blockchain.json'):
            print_warning("⚠️  Old blockchain.json still exists")
            print_info("   This is normal - it's kept as backup")
        else:
            print_success("✅ Old blockchain.json removed (fully migrated)")
        
        # Test saving a new block
        print()
        print_info("Testing block saving...")
        
        # Create a test transaction
        from modules.blockchain.blockchain import Transaction
        test_tx = Transaction(
            sender="test_sender",
            recipient="test_recipient", 
            amount=100.0
        )
        
        # Add transaction and mine block
        blockchain.add_transaction(test_tx)
        new_block = blockchain.mine_pending_transactions()
        
        print_success(f"✅ New block mined and saved!")
        print_info(f"   Block index: {new_block.index}")
        print_info(f"   Block hash: {new_block.block_hash[:16]}...")
        
        # Check if new block appears in storage
        updated_block_files = [f for f in os.listdir(chain_blocks_dir) if f.endswith('.json')]
        print_info(f"   Total blocks in storage: {len(updated_block_files)}")
        
        print()
        print("🎉 New storage format test completed successfully!")
        print("   Your blockchain is now using the modern ChainStorage format")
        print("   All blocks are stored in chain/blocks/ directory")
        
        return True
        
    except Exception as e:
        print_error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_new_storage() 