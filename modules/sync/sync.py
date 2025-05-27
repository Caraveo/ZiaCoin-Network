#!/usr/bin/env python3
import os
import sys
import subprocess
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class CodeSync:
    def __init__(self):
        self.repo_url = "https://github.com/Caraveo/ZiaCoin-Network.git"
        self.temp_dir = "temp_sync"
        self.current_dir = os.getcwd()
        self.repo_name = self.repo_url.split('/')[-1].replace('.git', '')
        
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
        self.current_version = self._load_version()

    def _load_version(self) -> Dict[str, Any]:
        """Load current version information."""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    return json.load(f)
            return {"version": "0.1.0", "files": {}}
        except Exception as e:
            logger.error(f"Error loading version: {e}")
            return {"version": "0.1.0", "files": {}}

    def get_local_hashes(self) -> Dict[str, str]:
        """Get SHA-256 hashes of local files."""
        hashes = {}
        for file_path in self.core_files:
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    hashes[file_path] = file_hash
            except FileNotFoundError:
                logger.warning(f"File not found: {file_path}")
        return hashes

    def get_remote_hashes(self) -> Dict[str, str]:
        """Get SHA-256 hashes of remote files."""
        try:
            # Clone or update repository
            if not os.path.exists(self.temp_dir):
                logger.info("Cloning repository...")
                subprocess.run(["git", "clone", self.repo_url, self.temp_dir], check=True)
            else:
                logger.info("Updating repository...")
                subprocess.run(["git", "-C", self.temp_dir, "pull"], check=True)
            
            # Get hashes from remote files
            hashes = {}
            for file_path in self.core_files:
                remote_path = os.path.join(self.temp_dir, file_path)
                try:
                    with open(remote_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        hashes[file_path] = file_hash
                except FileNotFoundError:
                    logger.warning(f"Remote file not found: {file_path}")
            
            return hashes
        except subprocess.CalledProcessError as e:
            logger.error(f"Error accessing remote repository: {str(e)}")
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
            remote_version_path = os.path.join(self.temp_dir, self.version_file)
            if os.path.exists(remote_version_path):
                with open(remote_version_path, 'r') as f:
                    remote_version = json.load(f).get('version')
            
            if not local_version or not remote_version:
                return False, "Version information not found"
            
            return local_version == remote_version, remote_version
        except Exception as e:
            logger.error(f"Error checking version: {str(e)}")
            return False, None

    def check_for_updates(self) -> bool:
        """Check if there are updates available."""
        try:
            # Compare files
            for root, _, files in os.walk(self.current_dir):
                for file in files:
                    if file.endswith('.py') or file.endswith('.conf'):
                        current_file = os.path.join(root, file)
                        temp_file = os.path.join(self.temp_dir, file)
                        
                        if os.path.exists(temp_file):
                            with open(current_file, 'r') as f1, open(temp_file, 'r') as f2:
                                if f1.read() != f2.read():
                                    logger.warning(f"File mismatch: {file}")
                                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False

    def update(self) -> bool:
        """Update the code to the latest version."""
        try:
            if not os.path.exists(self.temp_dir):
                logger.error("Repository not cloned. Run check_for_updates first.")
                return False

            # Copy updated files
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    if file.endswith('.py') or file.endswith('.conf'):
                        temp_file = os.path.join(root, file)
                        current_file = os.path.join(self.current_dir, file)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(current_file), exist_ok=True)
                        
                        # Copy file
                        with open(temp_file, 'r') as src, open(current_file, 'w') as dst:
                            dst.write(src.read())
                            logger.info(f"Updated {file}")

            # Clean up
            subprocess.run(["rm", "-rf", self.temp_dir], check=True)
            return True
        except Exception as e:
            logger.error(f"Error updating code: {e}")
            return False

    def sync(self) -> bool:
        """Check for updates and apply them if available."""
        try:
            if self.check_for_updates():
                logger.info("Code is not up to date.")
                return self.update()
            logger.info("Code is up to date.")
            return True
        except Exception as e:
            logger.error(f"Error during sync: {e}")
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
                    logger.warning(f"File mismatch: {file_path}")
                    return False
            
            # Check version
            version_match, remote_version = self.check_version()
            if not version_match:
                logger.warning(f"Version mismatch. Remote version: {remote_version}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            return False

    def check_sync(self) -> bool:
        """Check if code is in sync with version file."""
        try:
            current_files = self._get_file_hashes()
            return current_files == self.current_version.get("files", {})
        except Exception as e:
            logger.error(f"Error checking sync: {e}")
            return False

    def _get_file_hashes(self) -> Dict[str, str]:
        """Calculate SHA-256 hashes for all Python files."""
        file_hashes = {}
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                            file_hashes[file_path] = file_hash
                    except Exception as e:
                        logger.error(f"Error hashing {file_path}: {e}")
        return file_hashes

    def update_version(self):
        """Update version file with current file hashes."""
        try:
            current_files = self._get_file_hashes()
            self.current_version["files"] = current_files
            with open(self.version_file, 'w') as f:
                json.dump(self.current_version, f, indent=4)
            logger.info("Version file updated successfully")
        except Exception as e:
            logger.error(f"Error updating version: {e}")

def main():
    sync = CodeSync()
    if not sync.sync():
        print("Code synchronization failed. Please update manually.")
        sys.exit(1)
    print("Code synchronization completed successfully.")

if __name__ == "__main__":
    main() 