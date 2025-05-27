#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any
import requests

from modules.wallet.wallet import WalletManager
from modules.blockchain.blockchain import Blockchain
from modules.mnemonics.mnemonic import Mnemonic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_wallet_config() -> Dict[str, Any]:
    """Load configuration from wallet.conf file."""
    default_config = {
        "node": {
            "host": "localhost",
            "port": 8333,
            "api_endpoints": {
                "status": "/status",
                "balance": "/balance/{address}",
                "transaction": "/transaction",
                "chain": "/chain"
            }
        },
        "wallet": {
            "storage_path": "wallets/",
            "encryption": {
                "algorithm": "AES-GCM",
                "key_derivation": "PBKDF2",
                "iterations": 100000
            },
            "mnemonic": {
                "word_count": 12,
                "language": "english"
            }
        },
        "security": {
            "max_attempts": 3,
            "lockout_duration": 300,
            "session_timeout": 1800
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "wallet.log"
        }
    }
    
    try:
        if os.path.exists('wallet.conf'):
            with open('wallet.conf', 'r') as f:
                user_config = json.load(f)
                # Merge with defaults, keeping user values where provided
                for section in default_config:
                    if section in user_config:
                        default_config[section].update(user_config[section])
                logger.info("Loaded configuration from wallet.conf")
        else:
            logger.warning("No wallet.conf found, using default configuration")
            
        return default_config
    except Exception as e:
        logger.error(f"Error loading wallet config: {e}")
        logger.warning("Using default configuration")
        return default_config

def check_node_connection(config: Dict[str, Any]) -> bool:
    """Check if the node is running and accessible."""
    try:
        node_host = config['node']['host']
        node_port = config['node']['port']
        status_endpoint = config['node']['api_endpoints']['status']
        response = requests.get(f'http://{node_host}:{node_port}{status_endpoint}')
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to node. Please ensure the node is running.")
        return False

def create_wallet_record(args, config: Dict[str, Any]):
    """Create a new wallet with mnemonic and passphrase protection."""
    if not check_node_connection(config):
        sys.exit(1)
        
    wallet_manager = WalletManager(
        storage_path=config['wallet']['storage_path'],
        encryption_config=config['wallet']['encryption'],
        mnemonic_config=config['wallet']['mnemonic']
    )
    wallet = wallet_manager.create_wallet(args.name, args.passphrase)
    logger.info("\nNew Wallet Created:")
    logger.info(f"Name: {wallet.name}")
    logger.info(f"Address: {wallet.address}")
    logger.info(f"Public Key: {wallet.public_key}")
    logger.info(f"Mnemonic: {wallet.mnemonic}")
    logger.info("\nIMPORTANT: Save your mnemonic phrase securely!")
    logger.info("You will need it to recover your wallet if you lose access.")
    return wallet

def get_balance(args, config: Dict[str, Any]):
    """Get wallet balance."""
    if not check_node_connection(config):
        sys.exit(1)
        
    node_host = config['node']['host']
    node_port = config['node']['port']
    balance_endpoint = config['node']['api_endpoints']['balance'].format(address=args.address)
    
    try:
        response = requests.get(f'http://{node_host}:{node_port}{balance_endpoint}')
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Balance for {args.address}: {data['balance']} ZIA")
            return data['balance']
        else:
            logger.error(f"Failed to get balance: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return None

def send_transaction(args, config: Dict[str, Any]):
    """Send ZIA to another address."""
    if not check_node_connection(config):
        sys.exit(1)
        
    node_host = config['node']['host']
    node_port = config['node']['port']
    transaction_endpoint = config['node']['api_endpoints']['transaction']
    
    try:
        # Create transaction
        transaction = {
            'sender': args.from_address,
            'recipient': args.to_address,
            'amount': float(args.amount)
        }
        
        # Send transaction to node
        response = requests.post(
            f'http://{node_host}:{node_port}{transaction_endpoint}',
            json=transaction
        )
        
        if response.status_code == 200:
            logger.info(f"Sent {args.amount} ZIA from {args.from_address} to {args.to_address}")
            return transaction
        else:
            logger.error(f"Failed to send transaction: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error sending transaction: {e}")
        return None

def list_wallets(args, config: Dict[str, Any]):
    """List all wallets."""
    if not check_node_connection(config):
        sys.exit(1)
        
    wallet_manager = WalletManager(
        storage_path=config['wallet']['storage_path'],
        encryption_config=config['wallet']['encryption']
    )
    wallets = wallet_manager.list_wallets()
    for wallet in wallets:
        logger.info(f"Address: {wallet['address']}")
    return wallets

def recover_wallet(args, config: Dict[str, Any]):
    """Recover wallet from mnemonic phrase."""
    if not check_node_connection(config):
        sys.exit(1)
        
    wallet_manager = WalletManager(
        storage_path=config['wallet']['storage_path'],
        encryption_config=config['wallet']['encryption'],
        mnemonic_config=config['wallet']['mnemonic']
    )
    wallet = wallet_manager.recover_wallet(args.mnemonic, args.passphrase)
    logger.info("\nWallet Recovered:")
    logger.info(f"Name: {wallet.name}")
    logger.info(f"Address: {wallet.address}")
    logger.info(f"Public Key: {wallet.public_key}")
    return wallet

def load_wallet(args, config: Dict[str, Any]):
    """Load an existing wallet by address and passphrase."""
    if not check_node_connection(config):
        sys.exit(1)
        
    wallet_manager = WalletManager(
        storage_path=config['wallet']['storage_path'],
        encryption_config=config['wallet']['encryption']
    )
    wallet = wallet_manager.load_wallet(args.address, args.passphrase)
    logger.info("\nWallet Loaded:")
    logger.info(f"Name: {wallet.name}")
    logger.info(f"Address: {wallet.address}")
    logger.info(f"Public Key: {wallet.public_key}")
    return wallet

def main():
    # Load wallet configuration
    config = load_wallet_config()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        filename=config['logging']['file']
    )
    
    parser = argparse.ArgumentParser(description='ZiaCoin Wallet CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create wallet record command
    create_parser = subparsers.add_parser('createrecord', help='Create a new wallet with mnemonic')
    create_parser.add_argument('name', help='Name for the wallet')
    create_parser.add_argument('passphrase', help='Passphrase for wallet encryption')
    
    # Load wallet command
    load_parser = subparsers.add_parser('load', help='Load an existing wallet')
    load_parser.add_argument('address', help='Wallet address')
    load_parser.add_argument('passphrase', help='Wallet passphrase')
    
    # Get balance command
    balance_parser = subparsers.add_parser('balance', help='Get wallet balance')
    balance_parser.add_argument('address', help='Wallet address')
    
    # Send transaction command
    send_parser = subparsers.add_parser('send', help='Send ZIA to another address')
    send_parser.add_argument('from_address', help='Sender wallet address')
    send_parser.add_argument('to_address', help='Recipient wallet address')
    send_parser.add_argument('amount', help='Amount to send')
    
    # List wallets command
    list_parser = subparsers.add_parser('list', help='List all wallets')

    # Recover wallet command
    recover_parser = subparsers.add_parser('recover', help='Recover wallet from mnemonic')
    recover_parser.add_argument('mnemonic', help='Mnemonic phrase')
    recover_parser.add_argument('passphrase', help='Wallet passphrase')

    args = parser.parse_args()

    try:
        if args.command == 'createrecord':
            create_wallet_record(args, config)
        elif args.command == 'load':
            load_wallet(args, config)
        elif args.command == 'balance':
            get_balance(args, config)
        elif args.command == 'send':
            send_transaction(args, config)
        elif args.command == 'list':
            list_wallets(args, config)
        elif args.command == 'recover':
            recover_wallet(args, config)
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 