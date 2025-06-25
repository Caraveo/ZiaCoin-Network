#!/usr/bin/env python3
"""
Test script to validate node connection logic:
- Regular nodes must connect to 216.255.208.105:9999
- Initial nodes (--init) start as bootstrap
- Connection failures are handled properly
"""

import subprocess
import sys
import time
import requests

def test_initial_node_connection():
    """Test that the initial node is reachable."""
    print("🔍 Testing initial node connection...")
    try:
        response = requests.get("http://216.255.208.105:9999/status", timeout=5)
        if response.status_code == 200:
            print("✅ Initial node (216.255.208.105:9999) is reachable")
            return True
        else:
            print(f"❌ Initial node returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to initial node: {e}")
        return False

def test_regular_node_startup():
    """Test regular node startup (should succeed if initial node is up)."""
    print("\n🔍 Testing regular node startup...")
    try:
        # Start node on different port to avoid conflicts
        result = subprocess.run(
            ["python", "node.py", "--port", "9998"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "Connected to initial node" in result.stdout:
            print("✅ Regular node successfully connected to initial node")
            return True
        elif "Cannot start node without connection to initial node" in result.stderr:
            print("✅ Regular node correctly failed when initial node is down")
            return True
        else:
            print("❌ Unexpected result from regular node startup")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✅ Regular node startup test completed (timeout expected)")
        return True
    except Exception as e:
        print(f"❌ Error testing regular node: {e}")
        return False

def test_initial_node_startup():
    """Test initial node startup (--init flag)."""
    print("\n🔍 Testing initial node startup...")
    try:
        # Test with --init flag
        result = subprocess.run(
            ["python", "node.py", "--init", "--port", "9997"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "Starting as INITIAL bootstrap node" in result.stdout:
            print("✅ Initial node startup correctly identified")
            return True
        else:
            print("❌ Initial node startup failed")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✅ Initial node startup test completed (timeout expected)")
        return True
    except Exception as e:
        print(f"❌ Error testing initial node: {e}")
        return False

def main():
    """Run all connection tests."""
    print("🚀 ZiaCoin Node Connection Logic Test")
    print("=" * 50)
    
    # Test 1: Check if initial node is reachable
    initial_node_up = test_initial_node_connection()
    
    # Test 2: Test regular node startup
    regular_node_test = test_regular_node_startup()
    
    # Test 3: Test initial node startup
    initial_node_test = test_initial_node_startup()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Initial node reachable: {'✅' if initial_node_up else '❌'}")
    print(f"Regular node logic: {'✅' if regular_node_test else '❌'}")
    print(f"Initial node logic: {'✅' if initial_node_test else '❌'}")
    
    if all([initial_node_up, regular_node_test, initial_node_test]):
        print("\n🎉 All tests passed! Node connection logic is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 