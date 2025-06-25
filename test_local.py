#!/usr/bin/env python3
"""
Local test script for ZiaCoin Network Bootstrap Node
Tests only localhost connectivity for development
"""

import requests
import json
import sys

def test_local_node():
    """Test the bootstrap node on localhost."""
    base_url = "http://localhost:9999"
    
    print("🧪 Testing ZiaCoin Bootstrap Node (Local)...")
    print(f"📍 Testing node at: {base_url}")
    print()
    
    # Test 1: Node Status
    print("1️⃣ Testing node status...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Node is running!")
            print(f"   📊 Block height: {status.get('block_height', 'N/A')}")
            print(f"   🔗 Connected peers: {status.get('peers', 'N/A')}")
            print(f"   ⏳ Pending transactions: {status.get('pending_transactions', 'N/A')}")
        else:
            print(f"❌ Node returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to node. Is it running?")
        print("💡 Try: ./start_bootstrap.sh")
        return False
    except Exception as e:
        print(f"❌ Error testing node status: {e}")
        return False
    
    print()
    
    # Test 2: Blockchain Info
    print("2️⃣ Testing blockchain info...")
    try:
        response = requests.get(f"{base_url}/chain", timeout=5)
        if response.status_code == 200:
            chain_info = response.json()
            print(f"✅ Blockchain accessible!")
            print(f"   📏 Chain length: {chain_info.get('length', 'N/A')}")
            print(f"   🧱 Blocks: {len(chain_info.get('chain', []))}")
        else:
            print(f"❌ Failed to get blockchain: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing blockchain: {e}")
        return False
    
    print()
    
    # Test 3: Create Test Wallet
    print("3️⃣ Testing wallet creation...")
    try:
        response = requests.post(f"{base_url}/wallet/new", timeout=5)
        if response.status_code == 201:
            wallet = response.json()
            print(f"✅ Wallet created successfully!")
            print(f"   🏠 Address: {wallet.get('address', 'N/A')[:20]}...")
            print(f"   🔑 Public key: {wallet.get('public_key', 'N/A')[:20]}...")
        else:
            print(f"❌ Failed to create wallet: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing wallet creation: {e}")
        return False
    
    print()
    print("🎉 All local tests passed! Bootstrap node is working correctly.")
    print()
    print("📋 Local Node Information:")
    print(f"   🌐 Local access: {base_url}")
    print(f"   📊 Status: {base_url}/status")
    print(f"   ⛓️  Chain: {base_url}/chain")
    print(f"   💰 Wallet: {base_url}/wallet/new")
    print()
    print("🌐 For external access, ensure port 9999 is forwarded to your router.")
    print("🔗 External URL: http://216.255.208.105:9999")
    
    return True

if __name__ == "__main__":
    success = test_local_node()
    sys.exit(0 if success else 1) 