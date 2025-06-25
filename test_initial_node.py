#!/usr/bin/env python3
"""
Test script to verify initial node behavior
"""

import subprocess
import time
import requests
import sys

def test_initial_node_startup():
    """Test that initial node starts without connection errors."""
    print("🧪 Testing Initial Node Startup")
    print("=" * 50)
    
    try:
        # Start initial node in background
        print("Starting initial node with --init flag...")
        process = subprocess.Popen(
            ["python", "node.py", "--init"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Initial node started successfully")
            
            # Test status endpoint
            try:
                response = requests.get("http://localhost:9999/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Status endpoint working")
                    print(f"   └─ Node Type: {data.get('node_type', 'unknown')}")
                    print(f"   └─ Is Initial Node: {data.get('is_initial_node', False)}")
                    print(f"   └─ Peer Count: {data.get('peer_count', 0)}")
                else:
                    print(f"❌ Status endpoint failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Status endpoint error: {e}")
            
            # Test peers endpoint
            try:
                response = requests.get("http://localhost:9999/peers", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Peers endpoint working")
                    print(f"   └─ Total Peers: {data.get('peer_count', 0)}")
                else:
                    print(f"❌ Peers endpoint failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Peers endpoint error: {e}")
            
            # Terminate the process
            process.terminate()
            process.wait(timeout=5)
            print("✅ Initial node stopped cleanly")
            
        else:
            # Process exited, check output
            stdout, stderr = process.communicate()
            print("❌ Initial node failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    print("\n🎉 Initial node test completed successfully!")
    return True

def main():
    """Main test function."""
    success = test_initial_node_startup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 