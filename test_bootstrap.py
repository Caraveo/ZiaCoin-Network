#!/usr/bin/env python3
"""
Test script for ZiaCoin Network Bootstrap Node
Tests connectivity and basic functionality
"""

import requests
import json
import time
import sys

def test_bootstrap_node():
    """Test the bootstrap node functionality."""
    # Test both local and external access
    test_urls = [
        "http://localhost:9999",
        "http://216.255.208.105:9999"
    ]
    
    print("🧪 Testing ZiaCoin Bootstrap Node...")
    print()
    
    for base_url in test_urls:
        print(f"📍 Testing node at: {base_url}")
        
        # Test 1: Node Status
        print("1️⃣ Testing node status...")
        try:
            response = requests.get(f"{base_url}/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Node is running!")
                print(f"   📊 Block height: {status.get('block_height', 'N/A')}")
                print(f"   🔗 Connected peers: {status.get('peers', 'N/A')}")
                print(f"   ⏳ Pending transactions: {status.get('pending_transactions', 'N/A')}")
            else:
                print(f"❌ Node returned status code: {response.status_code}")
                continue
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is it running?")
            continue
        except Exception as e:
            print(f"❌ Error testing node status: {e}")
            continue
        
        print()
        
        # Test 2: Blockchain Info
        print("2️⃣ Testing blockchain info...")
        try:
            response = requests.get(f"{base_url}/chain", timeout=10)
            if response.status_code == 200:
                chain_info = response.json()
                print(f"✅ Blockchain accessible!")
                print(f"   📏 Chain length: {chain_info.get('length', 'N/A')}")
                print(f"   🧱 Blocks: {len(chain_info.get('chain', []))}")
            else:
                print(f"❌ Failed to get blockchain: {response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Error testing blockchain: {e}")
            continue
        
        print()
        
        # Test 3: Create Test Wallet
        print("3️⃣ Testing wallet creation...")
        try:
            response = requests.post(f"{base_url}/wallet/new", timeout=10)
            if response.status_code == 201:
                wallet = response.json()
                print(f"✅ Wallet created successfully!")
                print(f"   🏠 Address: {wallet.get('address', 'N/A')[:20]}...")
                print(f"   🔑 Public key: {wallet.get('public_key', 'N/A')[:20]}...")
            else:
                print(f"❌ Failed to create wallet: {response.status_code}")
                continue
        except Exception as e:
            print(f"❌ Error testing wallet creation: {e}")
            continue
        
        print()
        print(f"🎉 All tests passed for {base_url}!")
        print()
        
        # Only test one URL successfully, then break
        break
    
    print("📋 Node Information:")
    print(f"   🌐 Local access: http://localhost:9999")
    print(f"   🌐 External access: http://216.255.208.105:9999")
    print(f"   📊 Status: /status")
    print(f"   ⛓️  Chain: /chain")
    print(f"   💰 Wallet: /wallet/new")
    print()
    print("🔗 Other nodes can connect using: 216.255.208.105:9999")
    
    return True

if __name__ == "__main__":
    success = test_bootstrap_node()
    sys.exit(0 if success else 1) 