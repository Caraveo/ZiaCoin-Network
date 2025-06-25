#!/usr/bin/env python3
"""
ZiaCoin Network Mining Script
Start mining blocks and earn ZIA rewards
"""

import sys
import os
import time
import json
import requests
import argparse
import threading
from datetime import datetime

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.mining.miner import Miner
from modules.storage.chain_storage import ChainStorage
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

class MiningController:
    def __init__(self, node_url="http://localhost:9999", standalone=False):
        self.node_url = node_url
        self.standalone = standalone
        self.mining = False
        self.miner = None
        self.storage = None
        
        if standalone:
            self.storage = ChainStorage()
            self.miner = Miner(self.storage)
            self.miner.initialize()

    def start_mining(self):
        """Start the mining process."""
        if self.mining:
            print_warning("Mining is already running!")
            return
        
        self.mining = True
        print_success("🚀 Starting ZiaCoin mining...")
        
        if self.standalone:
            self._start_standalone_mining()
        else:
            self._start_node_mining()

    def _start_standalone_mining(self):
        """Start standalone mining without a node."""
        print_info("Running in standalone mode")
        
        # Create sample transactions
        transactions = [
            {
                'sender': 'network',
                'recipient': 'miner_reward',
                'amount': 50,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        # Start mining in background thread
        def mining_thread():
            while self.mining:
                try:
                    block = self.miner.mine_block(transactions)
                    if block:
                        print_success(f"✅ Block mined! Hash: {block.hash[:20]}...")
                        print_info(f"   📊 Block #{block.index}")
                        print_info(f"   ⏱️  Difficulty: {block.difficulty}")
                        print_info(f"   🔢 Nonce: {block.nonce}")
                        print_info(f"   💰 Reward: 50 ZIA")
                        print()
                except Exception as e:
                    print_error(f"Mining error: {e}")
                    time.sleep(1)
        
        threading.Thread(target=mining_thread, daemon=True).start()

    def _start_node_mining(self):
        """Start mining via node API."""
        print_info(f"Connecting to node: {self.node_url}")
        
        # Check if node is running
        try:
            response = requests.get(f"{self.node_url}/status", timeout=5)
            if response.status_code != 200:
                print_error("Node is not responding")
                return
        except Exception as e:
            print_error(f"Cannot connect to node: {e}")
            return
        
        # Start mining loop
        def mining_thread():
            while self.mining:
                try:
                    # Trigger mining via API
                    response = requests.post(f"{self.node_url}/mine", timeout=30)
                    if response.status_code == 201:
                        block_data = response.json()
                        print_success(f"✅ Block mined via node!")
                        print_info(f"   📊 Block: {block_data.get('block', {}).get('index', 'N/A')}")
                        print_info(f"   🔢 Hash: {block_data.get('block', {}).get('hash', 'N/A')[:20]}...")
                        print_info(f"   💰 Reward: 50 ZIA")
                        print()
                    else:
                        print_warning("No pending transactions to mine")
                        time.sleep(10)
                except Exception as e:
                    print_error(f"Mining error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=mining_thread, daemon=True).start()

    def stop_mining(self):
        """Stop the mining process."""
        if not self.mining:
            return
        
        self.mining = False
        if self.miner:
            self.miner.stop_mining()
        print_warning("⏹️ Mining stopped")

    def get_status(self):
        """Get current mining status."""
        if self.standalone and self.miner:
            status = self.miner.get_mining_status()
            print_info("📊 Mining Status:")
            print_info(f"   🔄 Mining: {'Yes' if status['mining'] else 'No'}")
            print_info(f"   📈 Difficulty: {status['difficulty']}")
            print_info(f"   🏗️  Height: {status['height']}")
        else:
            try:
                response = requests.get(f"{self.node_url}/status", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    print_info("📊 Node Status:")
                    print_info(f"   🔄 Status: {status.get('status', 'Unknown')}")
                    print_info(f"   📈 Block Height: {status.get('block_height', 'N/A')}")
                    print_info(f"   🔗 Peers: {status.get('peers', 'N/A')}")
                    print_info(f"   ⏳ Pending TX: {status.get('pending_transactions', 'N/A')}")
            except Exception as e:
                print_error(f"Error getting status: {e}")

def main():
    parser = argparse.ArgumentParser(description='ZiaCoin Network Miner')
    parser.add_argument('--node', default='http://localhost:9999', 
                       help='Node URL to connect to (default: http://localhost:9999)')
    parser.add_argument('--standalone', action='store_true',
                       help='Run in standalone mode without connecting to a node')
    parser.add_argument('--status', action='store_true',
                       help='Show mining status and exit')
    
    args = parser.parse_args()
    
    # Create mining controller
    controller = MiningController(args.node, args.standalone)
    
    if args.status:
        controller.get_status()
        return
    
    try:
        # Start mining
        controller.start_mining()
        
        print_info("💡 Press Ctrl+C to stop mining")
        print()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print()
        controller.stop_mining()
        print_success("👋 Mining session ended")

if __name__ == "__main__":
    main() 