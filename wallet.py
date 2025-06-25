#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any
import requests
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

from modules.wallet.wallet import WalletManager
from modules.blockchain.blockchain import Blockchain
from modules.mnemonics.mnemonic import Mnemonic
from modules.sync.sync import CodeSync
from modules.utils.print_utils import print_success, print_error, print_warning, print_info

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            record.msg = f"{self.COLORS[record.levelname]}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def load_wallet_config() -> Dict[str, Any]:
    """Load configuration from wallet.conf file."""
    default_config = {
        "node": {
            "host": "localhost",
            "port": 9999,
            "api_endpoints": {
                "status": "/status",
                "balance": "/balance/{address}",
                "transaction": "/transaction",
                "chain": "/chain"
            }
        },
        "wallet": {
            "storage_path": "chain/wallets/",
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
        },
        "updates": {
            "check_on_startup": False,
            "auto_update": False,
            "check_interval": 86400
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
                print_success("Configuration loaded successfully")
        else:
            print_warning("No wallet.conf found, using default configuration")
            
        return default_config
    except Exception as e:
        print_error(f"Error loading wallet config: {e}")
        print_warning("Using default configuration")
        return default_config

def check_node_connection(config: Dict[str, Any]) -> bool:
    """Check if the node is running and accessible."""
    try:
        # Check if this is a local connection
        if config['node']['host'] == 'localhost' and config['node']['port'] == 9999:
            # Try direct connection to node backend
            from modules.node_interface import is_local_node_available
            if is_local_node_available():
                print_success("Direct connection to node backend established")
                return True
            else:
                print_error("Local node backend not available. Is the node running?")
                return False
        else:
            # Remote connection - use HTTP
            response = requests.get(
                f"http://{config['node']['host']}:{config['node']['port']}/status",
                timeout=5
            )
            if response.status_code == 200:
                print_success("HTTP connection to node established")
                return True
            else:
                print_error(f"Node returned status code: {response.status_code}")
                return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to node. Is it running?")
        return False
    except requests.exceptions.Timeout:
        print_error("Node connection timed out")
        return False
    except Exception as e:
        print_error(f"Error connecting to node: {e}")
        return False

def create_wallet_record(args, config: Dict[str, Any]):
    """Create a new wallet with mnemonic and passphrase protection."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        wallet_manager = WalletManager(
            storage_path=config['wallet']['storage_path'],
            encryption_config=config['wallet']['encryption'],
            mnemonic_config=config['wallet']['mnemonic']
        )
        wallet = wallet_manager.create_wallet(args.name, args.passphrase)
        
        print_success("\nNew Wallet Created Successfully!")
        print_info(f"Name: {wallet.name}")
        print_info(f"Address: {wallet.address}")
        print_info(f"Public Key: {wallet.public_key}")
        print_warning("\nIMPORTANT: Save your mnemonic phrase securely!")
        print_warning("You will need it to recover your wallet if you lose access.")
        print_info(f"Mnemonic: {wallet.mnemonic}")
        return wallet
    except ValueError as e:
        print_error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to create wallet: {e}")
        sys.exit(1)

def load_wallet(args, config: Dict[str, Any]):
    """Load an existing wallet by address and passphrase."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        wallet_manager = WalletManager(
            storage_path=config['wallet']['storage_path'],
            encryption_config=config['wallet']['encryption']
        )
        wallet = wallet_manager.load_wallet(args.address, args.passphrase)
        
        print_success("\nWallet Loaded Successfully!")
        print_info(f"Name: {wallet.name}")
        print_info(f"Address: {wallet.address}")
        print_info(f"Public Key: {wallet.public_key}")
        return wallet
    except ValueError as e:
        print_error(f"Invalid passphrase or wallet not found: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to load wallet: {e}")
        sys.exit(1)

def get_balance(args, config: Dict[str, Any]):
    """Get wallet balance."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        # Check if this is a local connection
        if config['node']['host'] == 'localhost' and config['node']['port'] == 9999:
            # Use direct node interface
            from modules.node_interface import get_node_interface
            interface = get_node_interface()
            if interface:
                result = interface.get_balance(args.address)
                if 'error' in result:
                    print_error(f"Failed to get balance: {result['error']}")
                    sys.exit(1)
                balance = result['balance']
                print_success(f"\nBalance for {args.address}:")
                print_info(f"{balance} ZIA")
            else:
                print_error("Failed to get node interface")
                sys.exit(1)
        else:
            # Use HTTP API
            response = requests.get(
                f"http://{config['node']['host']}:{config['node']['port']}/balance/{args.address}",
                timeout=5
            )
            if response.status_code == 200:
                balance = response.json()['balance']
                print_success(f"\nBalance for {args.address}:")
                print_info(f"{balance} ZIA")
            else:
                print_error(f"Failed to get balance: {response.text}")
    except Exception as e:
        print_error(f"Error checking balance: {e}")
        sys.exit(1)

def send_transaction(args, config: Dict[str, Any]):
    """Send ZIA to another address."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        # Load sender's wallet
        wallet_manager = WalletManager(
            storage_path=config['wallet']['storage_path'],
            encryption_config=config['wallet']['encryption']
        )
        wallet = wallet_manager.load_wallet(args.from_address, args.passphrase)
        
        # Create transaction data
        transaction_data = {
            'sender': wallet.public_key,
            'recipient': args.to_address,
            'amount': float(args.amount),
            'private_key': wallet.private_key
        }
        
        # Check if this is a local connection
        if config['node']['host'] == 'localhost' and config['node']['port'] == 9999:
            # Use direct node interface
            from modules.node_interface import get_node_interface
            interface = get_node_interface()
            if interface:
                result = interface.create_transaction(transaction_data)
                if 'error' in result:
                    print_error(f"Failed to send transaction: {result['error']}")
                    sys.exit(1)
                print_success("\nTransaction Sent Successfully!")
                print_info(f"From: {args.from_address}")
                print_info(f"To: {args.to_address}")
                print_info(f"Amount: {args.amount} ZIA")
            else:
                print_error("Failed to get node interface")
                sys.exit(1)
        else:
            # Use HTTP API
            response = requests.post(
                f"http://{config['node']['host']}:{config['node']['port']}/transaction",
                json=transaction_data,
                timeout=5
            )
            
            if response.status_code == 201:
                print_success("\nTransaction Sent Successfully!")
                print_info(f"From: {args.from_address}")
                print_info(f"To: {args.to_address}")
                print_info(f"Amount: {args.amount} ZIA")
            else:
                print_error(f"Failed to send transaction: {response.text}")
    except ValueError as e:
        print_error(f"Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to send transaction: {e}")
        sys.exit(1)

def list_wallets(args, config: Dict[str, Any]):
    """List all wallets."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        wallet_manager = WalletManager(
            storage_path=config['wallet']['storage_path'],
            encryption_config=config['wallet']['encryption']
        )
        wallets = wallet_manager.list_wallets()
        
        if wallets:
            print_success("\nAvailable Wallets:")
            for wallet in wallets:
                print_info(f"Address: {wallet['address']}")
        else:
            print_warning("\nNo wallets found")
        return wallets
    except Exception as e:
        print_error(f"Failed to list wallets: {e}")
        sys.exit(1)

def recover_wallet(args, config: Dict[str, Any]):
    """Recover wallet from mnemonic phrase."""
    if not check_node_connection(config):
        print_error("No node connection. Wallet CLI will now exit.")
        sys.exit(1)
        
    try:
        wallet_manager = WalletManager(
            storage_path=config['wallet']['storage_path'],
            encryption_config=config['wallet']['encryption'],
            mnemonic_config=config['wallet']['mnemonic']
        )
        wallet = wallet_manager.recover_wallet(args.mnemonic, args.passphrase)
        
        print_success("\nWallet Recovered Successfully!")
        print_info(f"Name: {wallet.name}")
        print_info(f"Address: {wallet.address}")
        print_info(f"Public Key: {wallet.public_key}")
        return wallet
    except ValueError as e:
        print_error(f"Invalid mnemonic or passphrase: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to recover wallet: {e}")
        sys.exit(1)

def check_updates(config: Dict[str, Any]) -> None:
    """Check for updates based on configuration settings."""
    if not config['updates']['check_on_startup']:
        return
        
    try:
        sync = CodeSync()
        if sync.check_for_updates():
            if config['updates']['auto_update']:
                sync.update()
                print_success("Code updated successfully")
            else:
                print_warning("Updates available. Run with --update to apply them.")
    except Exception as e:
        print_error(f"Error checking for updates: {e}")

def main():
    # Load wallet configuration
    config = load_wallet_config()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        filename=config['logging']['file']
    )
    
    # Check for updates if configured
    check_updates(config)
    
    parser = argparse.ArgumentParser(description='ZiaCoin Wallet CLI')
    parser.add_argument('--update', action='store_true', help='Update to the latest version')
    parser.add_argument('--node', type=str, help='Remote API server address (host:port) - uses HTTP connection')
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
    send_parser.add_argument('passphrase', help='Sender wallet passphrase')
    
    # List wallets command
    list_parser = subparsers.add_parser('list', help='List all wallets')

    # Recover wallet command
    recover_parser = subparsers.add_parser('recover', help='Recover wallet from mnemonic')
    recover_parser.add_argument('mnemonic', help='Mnemonic phrase')
    recover_parser.add_argument('passphrase', help='Wallet passphrase')

    args = parser.parse_args()

    # Handle node configuration
    if args.node:
        try:
            # Parse remote API server address (host:port)
            if ':' in args.node:
                host, port_str = args.node.split(':', 1)
                port = int(port_str)
                config['node']['host'] = host
                config['node']['port'] = port
                print_info(f"Using remote API server: {host}:{port} (HTTP connection)")
            else:
                # If only host is provided, use default API port
                config['node']['host'] = args.node
                config['node']['port'] = 8000
                print_info(f"Using remote API server: {args.node}:8000 (HTTP connection)")
        except ValueError:
            print_error("Invalid API server format. Use host:port (e.g., localhost:8000 or 216.255.208.105:8000)")
            sys.exit(1)
    else:
        # Use local node backend by default (direct connection)
        if not config['node']['host'] or config['node']['host'] == '':
            config['node']['host'] = 'localhost'
            config['node']['port'] = 9999
            print_info("No remote server specified, using local node backend: localhost:9999 (direct connection)")
        else:
            print_info(f"Using configured node: {config['node']['host']}:{config['node']['port']}")
            if config['node']['host'] == 'localhost' and config['node']['port'] == 9999:
                print_info("Connecting directly to local node backend")
            else:
                print_info("Connecting to remote node via HTTP")

    try:
        if args.update:
            sync = CodeSync()
            sync.update()
            print_success("Code updated successfully")
            return
            
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
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 