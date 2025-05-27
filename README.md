# ZiaCoin Network

A modern, secure, and efficient blockchain implementation built with Python. ZiaCoin Network provides a robust foundation for decentralized applications with features like secure wallet management, efficient mining, and peer-to-peer networking.

## 🌟 Features

- **Secure Wallet Management**
  - Mnemonic phrase generation and recovery
  - Encrypted private key storage
  - Multiple wallet support
  - Easy wallet backup and restore
  - Configuration-based wallet settings

- **Efficient Mining System**
  - Proof-of-Work consensus
  - Dynamic difficulty adjustment
  - Merkle tree for transaction verification
  - Optimized block creation
  - Configurable mining parameters

- **Peer-to-Peer Networking**
  - Automatic node discovery
  - Real-time blockchain synchronization
  - Secure transaction broadcasting
  - Network health monitoring
  - HTTP API for wallet integration

- **Advanced Security**
  - AES-GCM encryption for private keys
  - Secure transaction signing
  - Chain integrity verification
  - Automatic code synchronization
  - Configurable security settings

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Caraveo/ZiaCoin-Network.git
cd ZiaCoin-Network
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

### Configuration

The network uses two configuration files:

1. `chain.config` - Node configuration:
```json
{
    "network": {
        "port": 9999,
        "bootstrap_nodes": []
    },
    "mining": {
        "difficulty": 4,
        "reward": 50
    },
    "wallet": {
        "storage_path": "wallets/"
    }
}
```

2. `wallet.conf` - Wallet configuration:
```json
{
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
```

### Basic Usage

1. **Start a Node**
```bash
# Start a node with default configuration
python3 node.py

# Start a node with custom port
python3 node.py --port 9999

# Start a node with specific bootstrap nodes
python3 node.py --bootstrap-nodes "127.0.0.1:9999,127.0.0.1:9998"

# Mine the genesis block
python3 node.py --genesis
```

2. **Create a Wallet**
```bash
python3 wallet.py createrecord "WalletName" "passphrase"
```

3. **Load an Existing Wallet**
```bash
python3 wallet.py load "wallet-address" "passphrase"
```

4. **Recover Wallet from Mnemonic**
```bash
python3 wallet.py recover "your-mnemonic-phrase" "passphrase"
```

5. **Check Wallet Balance**
```bash
python3 wallet.py balance "wallet-address"
```

6. **Send ZIA**
```bash
python3 wallet.py send "from-address" "to-address" "amount"
```

7. **List Wallets**
```bash
python3 wallet.py list
```

## 📚 API Endpoints

The node exposes the following HTTP API endpoints:

- `GET /status` - Get node status
- `GET /balance/{address}` - Get wallet balance
- `POST /transaction` - Create a new transaction
- `GET /chain` - Get the full blockchain

## 🔒 Security

- All private keys are encrypted using AES-GCM
- Transactions are signed using ECDSA
- Automatic code synchronization ensures you're running the latest secure version
- Regular security audits and updates
- Configurable security settings in wallet.conf

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Zia Open License v1.0.1 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by the Zia team
- Inspired by Bitcoin and Ethereum
- Special thanks to all contributors

## 📞 Support

For support, email hello@ziawe.com or join our Discord community. 