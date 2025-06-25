#!/usr/bin/env python3
"""
Peer Connection Monitor for ZiaCoin Network
Monitors and displays real-time peer connection information
"""

import requests
import time
import json
import sys
from datetime import datetime
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

class PeerMonitor:
    def __init__(self, node_url="http://localhost:9999"):
        self.node_url = node_url
        self.last_peer_count = 0
        
    def get_node_status(self):
        """Get node status and peer information."""
        try:
            response = requests.get(f"{self.node_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print_error(f"Failed to get status: HTTP {response.status_code}")
                return None
        except Exception as e:
            print_error(f"Error connecting to node: {e}")
            return None
    
    def get_peers(self):
        """Get detailed peer information."""
        try:
            response = requests.get(f"{self.node_url}/peers", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print_error(f"Failed to get peers: HTTP {response.status_code}")
                return None
        except Exception as e:
            print_error(f"Error getting peers: {e}")
            return None
    
    def get_network_stats(self):
        """Get network statistics."""
        try:
            response = requests.get(f"{self.node_url}/network/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print_error(f"Failed to get network stats: HTTP {response.status_code}")
                return None
        except Exception as e:
            print_error(f"Error getting network stats: {e}")
            return None
    
    def display_status(self, status_data):
        """Display node status information."""
        if not status_data:
            return
        
        print_info("=" * 60)
        print_info(f"📊 Node Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info("=" * 60)
        
        # Node information
        node_type = status_data.get('node_type', 'unknown')
        host = status_data.get('host', 'unknown')
        port = status_data.get('port', 'unknown')
        is_initial = status_data.get('is_initial_node', False)
        
        print_info(f"🏠 Node: {host}:{port}")
        print_info(f"📋 Type: {node_type.upper()}")
        print_info(f"🌐 Initial Node: {'Yes' if is_initial else 'No'}")
        
        # Blockchain information
        block_height = status_data.get('block_height', 0)
        pending_tx = status_data.get('pending_transactions', 0)
        
        print_info(f"📦 Block Height: {block_height}")
        print_info(f"⏳ Pending Transactions: {pending_tx}")
        
        # Peer information
        peer_count = status_data.get('peer_count', 0)
        peers = status_data.get('peers', [])
        
        print_info(f"🔗 Connected Peers: {peer_count}")
        
        # Check for new peers
        if peer_count > self.last_peer_count:
            print_success(f"🎉 New peer connected! Total: {peer_count}")
        elif peer_count < self.last_peer_count:
            print_warning(f"⚠️  Peer disconnected! Total: {peer_count}")
        
        self.last_peer_count = peer_count
        
        # Display peer details
        if peers:
            print_info("\n📋 Connected Peers:")
            for i, peer in enumerate(peers[:10], 1):  # Show first 10 peers
                host = peer.get('host', 'unknown')
                port = peer.get('port', 'unknown')
                status = peer.get('connection_status', 'unknown')
                height = peer.get('height', 0)
                last_seen = peer.get('time_since_last_seen', 0)
                is_initial = peer.get('is_initial_node', False)
                
                status_icon = "🟢" if status == "active" else "🔴"
                initial_icon = "⭐" if is_initial else "  "
                
                print_info(f"  {i:2d}. {status_icon} {initial_icon} {host}:{port}")
                print_info(f"      └─ Status: {status} | Height: {height} | Last seen: {last_seen:.1f}s ago")
            
            if len(peers) > 10:
                print_info(f"      ... and {len(peers) - 10} more peers")
        
        print_info("=" * 60)
    
    def display_network_stats(self, stats_data):
        """Display network statistics."""
        if not stats_data:
            return
        
        stats = stats_data.get('network_statistics', {})
        node_info = stats_data.get('node_info', {})
        
        print_info("📈 Network Statistics:")
        print_info(f"  └─ Total Peers: {stats.get('total_peers', 0)}")
        print_info(f"  └─ Active Peers: {stats.get('active_peers', 0)}")
        print_info(f"  └─ Inactive Peers: {stats.get('inactive_peers', 0)}")
        print_info(f"  └─ Connection Rate: {stats.get('connection_rate', '0/0')}")
        print_info(f"  └─ Initial Node Connected: {'Yes' if stats.get('initial_node_connected', False) else 'No'}")
    
    def monitor_loop(self, interval=10):
        """Main monitoring loop."""
        print_success("🚀 Starting ZiaCoin Peer Monitor")
        print_info(f"📡 Monitoring node: {self.node_url}")
        print_info(f"⏱️  Update interval: {interval} seconds")
        print_info("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                # Get and display status
                status_data = self.get_node_status()
                self.display_status(status_data)
                
                # Get and display network stats
                stats_data = self.get_network_stats()
                if stats_data:
                    self.display_network_stats(stats_data)
                
                print_info(f"⏳ Next update in {interval} seconds...\n")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print_warning("\n🛑 Monitoring stopped by user")
            sys.exit(0)
        except Exception as e:
            print_error(f"❌ Monitoring error: {e}")
            sys.exit(1)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZiaCoin Peer Connection Monitor')
    parser.add_argument('--node', default='http://localhost:9999', 
                       help='Node URL to monitor (default: http://localhost:9999)')
    parser.add_argument('--interval', type=int, default=10,
                       help='Update interval in seconds (default: 10)')
    
    args = parser.parse_args()
    
    # Create monitor and start
    monitor = PeerMonitor(args.node)
    monitor.monitor_loop(args.interval)

if __name__ == "__main__":
    main() 