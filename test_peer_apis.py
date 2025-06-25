#!/usr/bin/env python3
"""
Test script for peer-related API endpoints
"""

import requests
import json
import sys

def test_api_endpoint(url, endpoint, method="GET", data=None):
    """Test an API endpoint and return the response."""
    try:
        full_url = f"{url}{endpoint}"
        print(f"Testing {method} {full_url}")
        
        if method == "GET":
            response = requests.get(full_url, timeout=5)
        elif method == "POST":
            response = requests.post(full_url, json=data, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Success: {response.status_code}")
            return response.json()
        else:
            print(f"❌ Failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Test all peer-related API endpoints."""
    base_url = "http://localhost:9999"
    
    print("🧪 Testing ZiaCoin Peer API Endpoints")
    print("=" * 50)
    
    # Test 1: Status endpoint
    print("\n1. Testing /status endpoint:")
    status_data = test_api_endpoint(base_url, "/status")
    if status_data:
        print(f"   └─ Node Type: {status_data.get('node_type', 'unknown')}")
        print(f"   └─ Peer Count: {status_data.get('peer_count', 0)}")
        print(f"   └─ Block Height: {status_data.get('block_height', 0)}")
    
    # Test 2: Peers endpoint
    print("\n2. Testing /peers endpoint:")
    peers_data = test_api_endpoint(base_url, "/peers")
    if peers_data:
        print(f"   └─ Total Peers: {peers_data.get('peer_count', 0)}")
        peers = peers_data.get('peers', [])
        for i, peer in enumerate(peers[:3], 1):  # Show first 3 peers
            print(f"   └─ Peer {i}: {peer.get('host', 'unknown')}:{peer.get('port', 'unknown')}")
    
    # Test 3: Network endpoint
    print("\n3. Testing /network endpoint:")
    network_data = test_api_endpoint(base_url, "/network")
    if network_data:
        print(f"   └─ Network Status: {network_data.get('network_status', 'unknown')}")
        print(f"   └─ Total Peers: {network_data.get('total_peers', 0)}")
        print(f"   └─ Active Peers: {network_data.get('active_peers', 0)}")
        print(f"   └─ Initial Node Connected: {network_data.get('is_connected_to_initial', False)}")
    
    # Test 4: Network stats endpoint
    print("\n4. Testing /network/stats endpoint:")
    stats_data = test_api_endpoint(base_url, "/network/stats")
    if stats_data:
        stats = stats_data.get('network_statistics', {})
        print(f"   └─ Connection Rate: {stats.get('connection_rate', '0/0')}")
        print(f"   └─ Initial Node Connected: {stats.get('initial_node_connected', False)}")
    
    # Test 5: Manual peer connection (will likely fail if peer doesn't exist)
    print("\n5. Testing /peers/connect endpoint:")
    test_peer_data = {"host": "192.168.1.100", "port": 9998}
    connect_result = test_api_endpoint(base_url, "/peers/connect", method="POST", data=test_peer_data)
    if connect_result:
        print(f"   └─ Result: {connect_result.get('status', 'unknown')}")
    
    print("\n" + "=" * 50)
    print("🎉 API endpoint testing completed!")

if __name__ == "__main__":
    main() 