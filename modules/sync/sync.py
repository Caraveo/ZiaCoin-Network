#!/usr/bin/env python3
import os
import sys
import subprocess
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime

class CodeSync:
    def __init__(self, repo_url: str = "https://github.com/caraveo/ZiaCoin-Network.git"):
        self.repo_url = repo_url
        self.repo_name = repo_url.split('/')[-1].replace('.git', '')
        self.logger = logging.getLogger("CodeSync")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Core files to check
        self.core_files = [
            'wallet.py',
            'blockchain.py',
            'miner.py',
            'app.py',
            'modules/encryption/encryption.py'
        ]
        
        # Version file
        self.version_file = 'version.json'

    def get_local_hashes(self) -> Dict[str, str]:
        """Get SHA-256 hashes of local files."""
        hashes = {}
        for file_path in self.core_files:
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    hashes[file_path] = file_hash
            except FileNotFoundError:
                self.logger.warning(f"File not found: {file_path}")
        return hashes

    def get_remote_hashes(self) -> Dict[str, str]:
        """Get SHA-256 hashes of remote files."""
        try:
            # Clone or update repository
            if not os.path.exists(self.repo_name):
                subprocess.run(['git', 'clone', self.repo_url], check=True)
            else:
                subprocess.run(['git', '-C', self.repo_name, 'pull'], check=True)
            
            # Get hashes from remote files
            hashes = {}
            for file_path in self.core_files:
                remote_path = os.path.join(self.repo_name, file_path)
                try:
                    with open(remote_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        hashes[file_path] = file_hash
                except FileNotFoundError:
                    self.logger.warning(f"Remote file not found: {file_path}")
            
            return hashes
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error accessing remote repository: {str(e)}")
            return {}

    def check_version(self) -> Tuple[bool, Optional[str]]:
        """Check if local version matches remote version."""
        try:
            # Get local version
            local_version = None
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    local_version = json.load(f).get('version')
            
            # Get remote version
            remote_version = None
            remote_version_path = os.path.join(self.repo_name, self.version_file)
            if os.path.exists(remote_version_path):
                with open(remote_version_path, 'r') as f:
                    remote_version = json.load(f).get('version')
            
            if not local_version or not remote_version:
                return False, "Version information not found"
            
            return local_version == remote_version, remote_version
        except Exception as e:
            self.logger.error(f"Error checking version: {str(e)}")
            return False, None

    def update_code(self) -> bool:
        """Update local code from remote repository."""
        try:
            # Get remote hashes
            remote_hashes = self.get_remote_hashes()
            if not remote_hashes:
                return False
            
            # Update each file
            for file_path, remote_hash in remote_hashes.items():
                remote_file = os.path.join(self.repo_name, file_path)
                if os.path.exists(remote_file):
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Copy file
                    with open(remote_file, 'rb') as src, open(file_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    self.logger.info(f"Updated {file_path}")
            
            # Update version file
            remote_version_path = os.path.join(self.repo_name, self.version_file)
            if os.path.exists(remote_version_path):
                with open(remote_version_path, 'rb') as src, open(self.version_file, 'wb') as dst:
                    dst.write(src.read())
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating code: {str(e)}")
            return False

    def verify_code(self) -> bool:
        """Verify that all core files are up to date."""
        try:
            # Get local and remote hashes
            local_hashes = self.get_local_hashes()
            remote_hashes = self.get_remote_hashes()
            
            if not remote_hashes:
                return False
            
            # Check if all files match
            for file_path, remote_hash in remote_hashes.items():
                local_hash = local_hashes.get(file_path)
                if not local_hash or local_hash != remote_hash:
                    self.logger.warning(f"File mismatch: {file_path}")
                    return False
            
            # Check version
            version_match, remote_version = self.check_version()
            if not version_match:
                self.logger.warning(f"Version mismatch. Remote version: {remote_version}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error verifying code: {str(e)}")
            return False

    def sync(self) -> bool:
        """Synchronize code with remote repository."""
        try:
            # Check if code is up to date
            if self.verify_code():
                self.logger.info("Code is up to date")
                return True
            
            # Ask user for update
            print("\nCode is not up to date. Would you like to update? (y/n)")
            response = input().lower()
            
            if response == 'y':
                if self.update_code():
                    self.logger.info("Code updated successfully")
                    return True
                else:
                    self.logger.error("Failed to update code")
                    return False
            else:
                self.logger.warning("Update declined by user")
                return False
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            return False

def main():
    sync = CodeSync()
    if not sync.sync():
        print("Code synchronization failed. Please update manually.")
        sys.exit(1)
    print("Code synchronization completed successfully.")

if __name__ == "__main__":
    main() 