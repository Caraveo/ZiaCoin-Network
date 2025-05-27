#!/usr/bin/env python3
import boto3
import subprocess
import json
import time
import os
from typing import List, Dict
import logging
from pathlib import Path

class ZiaCoinKubernetes:
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.logger = logging.getLogger("ZiaCoinKubernetes")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configuration
        self.instance_type = "t3.micro"  # Minimal instance type
        self.ami_id = "ami-0735c191cf914754d"  # Ubuntu 20.04 LTS
        self.key_name = "ziacoin-nodes"
        self.security_group_name = "ziacoin-nodes-sg"
        self.node_count = 5
        self.nodes: List[Dict] = []

    def create_key_pair(self):
        """Create an EC2 key pair for node access."""
        try:
            key_pair = self.ec2.create_key_pair(
                KeyName=self.key_name,
                TagSpecifications=[
                    {
                        'ResourceType': 'key-pair',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'ZiaCoin Nodes'
                            }
                        ]
                    }
                ]
            )
            
            # Save private key
            private_key_path = Path.home() / '.ssh' / f'{self.key_name}.pem'
            with open(private_key_path, 'w') as f:
                f.write(key_pair['KeyMaterial'])
            
            # Set proper permissions
            os.chmod(private_key_path, 0o400)
            
            self.logger.info(f"Created key pair: {self.key_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating key pair: {str(e)}")
            return False

    def create_security_group(self):
        """Create a security group for the nodes."""
        try:
            security_group = self.ec2.create_security_group(
                GroupName=self.security_group_name,
                Description='Security group for ZiaCoin nodes'
            )
            
            # Allow SSH access
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group['GroupId'],
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 8333,
                        'ToPort': 8333,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            self.logger.info(f"Created security group: {self.security_group_name}")
            return security_group['GroupId']
        except Exception as e:
            self.logger.error(f"Error creating security group: {str(e)}")
            return None

    def create_elastic_ips(self) -> List[str]:
        """Create Elastic IPs for the nodes."""
        eip_ids = []
        for _ in range(self.node_count):
            try:
                eip = self.ec2.allocate_address(
                    Domain='vpc',
                    TagSpecifications=[
                        {
                            'ResourceType': 'elastic-ip',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    'Value': 'ZiaCoin Node'
                                }
                            ]
                        }
                    ]
                )
                eip_ids.append(eip['AllocationId'])
                self.logger.info(f"Created Elastic IP: {eip['PublicIp']}")
            except Exception as e:
                self.logger.error(f"Error creating Elastic IP: {str(e)}")
        return eip_ids

    def create_instances(self, security_group_id: str, eip_ids: List[str]):
        """Create EC2 instances for the nodes."""
        try:
            # User data script for instance initialization
            user_data = """#!/bin/bash
apt-get update
apt-get install -y git python3-pip
git clone https://github.com/your-org/ZiaCoin-Network.git
cd ZiaCoin-Network/chain
pip3 install -r requirements.txt
python3 wallet.py createrecord "Node" "secure-passphrase"
"""
            
            # Create instances
            instances = self.ec2_resource.create_instances(
                ImageId=self.ami_id,
                InstanceType=self.instance_type,
                MinCount=self.node_count,
                MaxCount=self.node_count,
                KeyName=self.key_name,
                SecurityGroupIds=[security_group_id],
                UserData=user_data,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'ZiaCoin Node'
                            }
                        ]
                    }
                ]
            )
            
            # Wait for instances to be running
            for instance in instances:
                instance.wait_until_running()
            
            # Associate Elastic IPs
            for instance, eip_id in zip(instances, eip_ids):
                self.ec2.associate_address(
                    InstanceId=instance.id,
                    AllocationId=eip_id
                )
                self.nodes.append({
                    'instance_id': instance.id,
                    'public_ip': instance.public_ip_address,
                    'private_ip': instance.private_ip_address
                })
            
            self.logger.info(f"Created {len(instances)} instances")
            return True
        except Exception as e:
            self.logger.error(f"Error creating instances: {str(e)}")
            return False

    def configure_nodes(self):
        """Configure the nodes to work together."""
        try:
            # Create node configuration file
            config = {
                'nodes': [
                    {
                        'host': node['public_ip'],
                        'port': 8333,
                        'is_bootstrap': i == 0  # First node is bootstrap
                    }
                    for i, node in enumerate(self.nodes)
                ]
            }
            
            # Save configuration
            with open('node_config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            # Copy configuration to each node
            for node in self.nodes:
                subprocess.run([
                    'scp',
                    '-i', f'{Path.home()}/.ssh/{self.key_name}.pem',
                    'node_config.json',
                    f'ubuntu@{node["public_ip"]}:~/ZiaCoin-Network/chain/config.json'
                ])
            
            self.logger.info("Configured nodes")
            return True
        except Exception as e:
            self.logger.error(f"Error configuring nodes: {str(e)}")
            return False

    def deploy(self):
        """Deploy the ZiaCoin node cluster."""
        # Create key pair
        if not self.create_key_pair():
            return False
        
        # Create security group
        security_group_id = self.create_security_group()
        if not security_group_id:
            return False
        
        # Create Elastic IPs
        eip_ids = self.create_elastic_ips()
        if not eip_ids:
            return False
        
        # Create instances
        if not self.create_instances(security_group_id, eip_ids):
            return False
        
        # Configure nodes
        if not self.configure_nodes():
            return False
        
        self.logger.info("Deployment completed successfully")
        return True

    def get_node_info(self):
        """Get information about the deployed nodes."""
        return self.nodes

def main():
    kuber = ZiaCoinKubernetes()
    if kuber.deploy():
        print("\nDeployed Nodes:")
        for i, node in enumerate(kuber.get_node_info()):
            print(f"\nNode {i + 1}:")
            print(f"  Public IP: {node['public_ip']}")
            print(f"  Private IP: {node['private_ip']}")
            print(f"  Instance ID: {node['instance_id']}")
    else:
        print("Deployment failed")

if __name__ == "__main__":
    main() 