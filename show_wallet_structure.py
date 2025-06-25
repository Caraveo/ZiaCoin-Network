#!/usr/bin/env python3
"""
Show Wallet Directory Structure
This script shows where different types of wallets are stored
"""

import os
import json

def show_wallet_structure():
    """Show the wallet directory structure."""
    
    print("📁 Wallet Directory Structure")
    print("=" * 50)
    print()
    
    # Check main wallets directory
    wallets_dir = "wallets"
    if os.path.exists(wallets_dir):
        wallet_files = [f for f in os.listdir(wallets_dir) if f.endswith('.wallet')]
        print(f"📂 {wallets_dir}/: {len(wallet_files)} regular wallets")
        for file in wallet_files:
            print(f"   - {file}")
    else:
        print(f"📂 {wallets_dir}/: Directory not found")
    
    print()
    
    # Check chain/wallets directory
    chain_wallets_dir = "chain/wallets"
    if os.path.exists(chain_wallets_dir):
        wallet_files = [f for f in os.listdir(chain_wallets_dir) if f.endswith('.wallet')]
        print(f"📂 {chain_wallets_dir}/: {len(wallet_files)} chain wallets")
        for file in wallet_files:
            print(f"   - {file}")
    else:
        print(f"📂 {chain_wallets_dir}/: Directory not found")
    
    print()
    
    # Check chain/restored directory
    chain_restored_dir = "chain/restored"
    if os.path.exists(chain_restored_dir):
        wallet_files = [f for f in os.listdir(chain_restored_dir) if f.endswith('.wallet')]
        print(f"📂 {chain_restored_dir}/: {len(wallet_files)} recovered wallets")
        for file in wallet_files:
            print(f"   - {file}")
    else:
        print(f"📂 {chain_restored_dir}/: Directory not found")
    
    print()
    
    # Check wallet index
    wallet_index_file = "wallets/index.json"
    if os.path.exists(wallet_index_file):
        try:
            with open(wallet_index_file, 'r') as f:
                index_data = json.load(f)
                wallets = index_data.get('wallets', {})
                print(f"📄 Wallet Index ({wallet_index_file}): {len(wallets)} wallets registered")
                
                # Count by type
                regular_count = 0
                recovered_count = 0
                for wallet_info in wallets.values():
                    if wallet_info.get('type') == 'recovered':
                        recovered_count += 1
                    else:
                        regular_count += 1
                
                print(f"   - Regular wallets: {regular_count}")
                print(f"   - Recovered wallets: {recovered_count}")
                
        except Exception as e:
            print(f"📄 Wallet Index: Error reading file - {e}")
    else:
        print(f"📄 Wallet Index: File not found")
    
    print()
    print("📋 Summary:")
    print("   - Regular wallets: Created normally, stored in wallets/ or chain/wallets/")
    print("   - Recovered wallets: Recovered from mnemonics, stored in chain/restored/")
    print("   - All wallet files are encrypted and protected")
    print("   - Wallet index tracks all wallets regardless of location")

if __name__ == "__main__":
    show_wallet_structure() 