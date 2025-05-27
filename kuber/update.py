#!/usr/bin/env python3
import boto3
import subprocess
import json
import time
from typing import List, Dict
import logging
from pathlib import Path

class ZiaCoinUpdater:
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.logger = logging.getLogger("ZiaCoinUpdater")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configuration
        self.key_name = "ziacoin-nodes"
        self.nodes: List[Dict] = []

    def load_node_info(self):
        """Load information about deployed nodes."""
        try:
            # Get instances with the ZiaCoin Node tag
            response = self.ec2.describe_instances(
                Filters=[
                    {
                        'Name': 'tag:Name',
                        'Values': ['ZiaCoin Node']
                    },
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running']
                    }
                ]
            )
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    self.nodes.append({
                        'instance_id': instance['InstanceId'],
                        'public_ip': instance['PublicIpAddress'],
                        'private_ip': instance['PrivateIpAddress']
                    })
            
            self.logger.info(f"Loaded information for {len(self.nodes)} nodes")
            return True
        except Exception as e:
            self.logger.error(f"Error loading node information: {str(e)}")
            return False

    def update_code(self):
        """Update the code on all nodes."""
        try:
            for node in self.nodes:
                # Pull latest code
                subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'cd ~/ZiaCoin-Network && git pull'
                ])
                
                # Install dependencies
                subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'cd ~/ZiaCoin-Network/chain && pip3 install -r requirements.txt'
                ])
                
                self.logger.info(f"Updated code on node {node['public_ip']}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating code: {str(e)}")
            return False

    def restart_nodes(self):
        """Restart the blockchain nodes."""
        try:
            for node in self.nodes:
                # Stop any running node processes
                subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'pkill -f "python3.*wallet.py" || true'
                ])
                
                # Start the node
                subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'cd ~/ZiaCoin-Network/chain && nohup python3 wallet.py start > node.log 2>&1 &'
                ])
                
                self.logger.info(f"Restarted node {node['public_ip']}")
            return True
        except Exception as e:
            self.logger.error(f"Error restarting nodes: {str(e)}")
            return False

    def check_node_status(self):
        """Check the status of all nodes."""
        try:
            for node in self.nodes:
                # Check if node process is running
                result = subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'pgrep -f "python3.*wallet.py"'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info(f"Node {node['public_ip']} is running")
                else:
                    self.logger.warning(f"Node {node['public_ip']} is not running")
            return True
        except Exception as e:
            self.logger.error(f"Error checking node status: {str(e)}")
            return False

    def get_node_logs(self):
        """Get logs from all nodes."""
        try:
            for node in self.nodes:
                # Get the last 100 lines of the log
                result = subprocess.run([
                    'ssh',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    f'ubuntu@{node["public_ip"]}',
                    'tail -n 100 ~/ZiaCoin-Network/chain/node.log'
                ], capture_output=True, text=True)
                
                print(f"\nLogs from node {node['public_ip']}:")
                print(result.stdout)
            return True
        except Exception as e:
            self.logger.error(f"Error getting node logs: {str(e)}")
            return False

    def update(self):
        """Update the entire node cluster."""
        if not self.load_node_info():
            return False
        
        if not self.update_code():
            return False
        
        if not self.restart_nodes():
            return False
        
        # Wait for nodes to start
        time.sleep(10)
        
        if not self.check_node_status():
            return False
        
        self.logger.info("Update completed successfully")
        return True

def main():
    updater = ZiaCoinUpdater()
    if updater.update():
        print("\nUpdate completed successfully")
        print("\nNode Logs:")
        updater.get_node_logs()
    else:
        print("Update failed")

if __name__ == "__main__":
    main() 