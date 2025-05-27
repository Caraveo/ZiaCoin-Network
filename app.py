from flask import Flask, request, jsonify
from blockchain import Blockchain, Transaction
from wallet import Wallet
import json
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    app.run(host='0.0.0.0', port=5000, debug=True)