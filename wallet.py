#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

from modules.wallet.wallet import WalletManager
from modules.blockchain.blockchain import Blockchain
from modules.mnemonics.mnemonic import Mnemonic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from chain.config file."""
    try:
        if os.path.exists('chain.config'):
            with open('chain.config', 'r') as f:
                return json.load(f)
        else:
            logger.error("chain.config not found")
            return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def create_wallet_record(args):
    """Create a new wallet with mnemonic and passphrase protection."""
    wallet_manager = WalletManager()
    wallet = wallet_manager.create_wallet(args.name, args.passphrase)
    logger.info("\nNew Wallet Created:")
    logger.info(f"Name: {wallet.name}")
    logger.info(f"Address: {wallet.address}")
    logger.info(f"Public Key: {wallet.public_key}")
    logger.info(f"Mnemonic: {wallet.mnemonic}")
    logger.info("\nIMPORTANT: Save your mnemonic phrase securely!")
    logger.info("You will need it to recover your wallet if you lose access.")
    return wallet

def get_balance(args):
    """Get wallet balance."""
    blockchain = Blockchain()
    balance = blockchain.get_balance(args.address)
    logger.info(f"Balance for {args.address}: {balance} ZIA")
    return balance

def send_transaction(args):
    """Send ZIA to another address."""
    wallet_manager = WalletManager()
    blockchain = Blockchain()
    
    # Create transaction
    transaction = {
        'sender': args.from_address,
        'recipient': args.to_address,
        'amount': float(args.amount)
    }
    
    # Sign transaction
    wallet_manager.sign_transaction(transaction, args.from_address)
    
    # Add to blockchain
    blockchain.add_transaction(transaction)
    logger.info(f"Sent {args.amount} ZIA from {args.from_address} to {args.to_address}")
    return transaction

def list_wallets(args):
    """List all wallets."""
    wallet_manager = WalletManager()
    wallets = wallet_manager.list_wallets()
    for wallet in wallets:
        logger.info(f"Address: {wallet['address']}")
    return wallets

def recover_wallet(args):
    """Recover wallet from mnemonic phrase."""
    wallet_manager = WalletManager()
    wallet = wallet_manager.recover_wallet(args.mnemonic, args.passphrase)
    logger.info("\nWallet Recovered:")
    logger.info(f"Name: {wallet.name}")
    logger.info(f"Address: {wallet.address}")
    logger.info(f"Public Key: {wallet.public_key}")
    return wallet

def main():
    parser = argparse.ArgumentParser(description='ZiaCoin Wallet CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create wallet record command
    create_parser = subparsers.add_parser('createrecord', help='Create a new wallet with mnemonic')
    create_parser.add_argument('name', help='Name for the wallet')
    create_parser.add_argument('passphrase', help='Passphrase for wallet encryption')
    
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
            create_wallet_record(args)
        elif args.command == 'balance':
            get_balance(args)
        elif args.command == 'send':
            send_transaction(args)
        elif args.command == 'list':
            list_wallets(args)
        elif args.command == 'recover':
            recover_wallet(args)
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 