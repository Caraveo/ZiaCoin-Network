#!/usr/bin/env python3
import sys
import os
import json
import logging
from typing import Dict, Any

# Suppress Flask development server warning
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import the sync module
from modules.sync.sync import CodeSync

def load_config() -> Dict[str, Any]:
    """Load configuration from app.conf file."""
    default_config = {
        "updates": {
            "check_on_startup": False,
            "auto_update": False,
            "check_interval": 86400
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "app.log"
        }
    }
    
    try:
        if os.path.exists('app.conf'):
            with open('app.conf', 'r') as f:
                user_config = json.load(f)
                # Merge with defaults, keeping user values where provided
                for section in default_config:
                    if section in user_config:
                        default_config[section].update(user_config[section])
                logger.info("Loaded configuration from app.conf")
        else:
            logger.warning("No app.conf found, using default configuration")
            
        return default_config
    except Exception as e:
        logger.error(f"Error loading app config: {e}")
        logger.warning("Using default configuration")
        return default_config

def check_updates(config: Dict[str, Any]) -> None:
    """Check for updates based on configuration settings."""
    if not config['updates']['check_on_startup']:
        return
        
    try:
        sync = CodeSync()
        if sync.check_for_updates():
            if config['updates']['auto_update']:
                sync.update()
                logger.info("Code updated successfully")
            else:
                logger.info("Updates available. Run with --update to apply them.")
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Check for updates if configured
check_updates(config)

from flask import Flask, request, jsonify
from blockchain import Blockchain, Transaction
from wallet import Wallet

app = Flask(__name__)

# Initialize the blockchain
blockchain = Blockchain()

@app.route('/wallet/new', methods=['POST'])
def new_wallet() -> tuple[Dict[str, Any], int]:
    """Create a new wallet."""
    try:
        wallet = Wallet.create()
        return jsonify({
            'address': wallet.address,
            'public_key': wallet.public_key,
            'private_key': wallet.private_key
        }), 201
    except Exception as e:
        logger.error(f"Failed to create wallet: {str(e)}")
        return jsonify({'error': 'Failed to create wallet'}), 500

@app.route('/transaction/new', methods=['POST'])
def new_transaction() -> tuple[Dict[str, Any], int]:
    """Create a new transaction."""
    try:
        data = request.get_json()
        if not all(k in data for k in ['sender', 'recipient', 'amount', 'private_key']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Create and sign transaction
        transaction = Transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=float(data['amount'])
        )
        transaction.sign(data['private_key'])

        # Add transaction to blockchain
        block_index = blockchain.add_transaction(transaction)
        
        return jsonify({
            'message': f'Transaction will be added to Block {block_index}',
            'transaction': transaction.to_dict()
        }), 201
    except ValueError as e:
        logger.error(f"Invalid transaction: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create transaction: {str(e)}")
        return jsonify({'error': 'Failed to create transaction'}), 500

@app.route('/mine', methods=['POST'])
def mine() -> tuple[Dict[str, Any], int]:
    """Mine a new block."""
    try:
        if not blockchain.pending_transactions:
            return jsonify({'error': 'No pending transactions to mine'}), 400

        block = blockchain.mine_pending_transactions()
        return jsonify({
            'message': 'New Block Forged',
            'block': block.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Failed to mine block: {str(e)}")
        return jsonify({'error': 'Failed to mine block'}), 500

@app.route('/chain', methods=['GET'])
def get_chain() -> tuple[Dict[str, Any], int]:
    """Get the full blockchain."""
    try:
        return jsonify({
            'chain': [block.to_dict() for block in blockchain.chain],
            'length': len(blockchain.chain)
        }), 200
    except Exception as e:
        logger.error(f"Failed to get chain: {str(e)}")
        return jsonify({'error': 'Failed to get chain'}), 500

@app.route('/validate', methods=['GET'])
def validate_chain() -> tuple[Dict[str, Any], int]:
    """Validate the blockchain."""
    try:
        is_valid = blockchain.is_chain_valid()
        return jsonify({
            'is_valid': is_valid,
            'message': 'Chain is valid' if is_valid else 'Chain is invalid'
        }), 200
    except Exception as e:
        logger.error(f"Failed to validate chain: {str(e)}")
        return jsonify({'error': 'Failed to validate chain'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False,  # Disable debug mode in production
        threaded=True,  # Enable threading for better performance
        use_reloader=False,  # Disable reloader to prevent duplicate processes
        passthrough_errors=True  # Pass through errors instead of handling them
    )