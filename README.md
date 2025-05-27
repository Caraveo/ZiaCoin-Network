# ZiaCoin Network

A modern, secure, and efficient blockchain implementation built with Python. ZiaCoin Network provides a robust foundation for decentralized applications with features like secure wallet management, efficient mining, and peer-to-peer networking.

## 🌟 Features

- **Secure Wallet Management**
  - Mnemonic phrase generation and recovery
  - Encrypted private key storage
  - Multiple wallet support
  - Easy wallet backup and restore

- **Efficient Mining System**
  - Proof-of-Work consensus
  - Dynamic difficulty adjustment
  - Merkle tree for transaction verification
  - Optimized block creation

- **Peer-to-Peer Networking**
  - Automatic node discovery
  - Real-time blockchain synchronization
  - Secure transaction broadcasting
  - Network health monitoring

- **Advanced Security**
  - AES-GCM encryption for private keys
  - Secure transaction signing
  - Chain integrity verification
  - Automatic code synchronization

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Caraveo/ZiaCoin-Network.git
cd ZiaCoin-Network/chain
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Create your first wallet:
```bash
python3 wallet.py createrecord "MyWallet" "your-secure-passphrase"
```

### Basic Usage

1. **Start a Node**
```bash
# Start a node with default configuration
python3 node.py

# Start a node with custom port
python3 node.py --port 8334

# Start a node with specific bootstrap nodes
python3 node.py --bootstrap-nodes "127.0.0.1:8333,127.0.0.1:8334"
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

5. **Start Mining**
```bash
python3 miner.py
```

6. **Run the API Server**
```bash
python3 app.py
```

## 🔧 Configuration

Create a `chain.config` file in the root directory with your settings:

```json
{
    "network": {
        "port": 8333,
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

## 📚 API Endpoints

- `POST /wallet/new` - Create a new wallet
- `POST /transaction/new` - Create a new transaction
- `POST /mine` - Mine a new block
- `GET /chain` - Get the full blockchain
- `GET /validate` - Validate the blockchain

## 🔒 Security

- All private keys are encrypted using AES-GCM
- Transactions are signed using ECDSA
- Automatic code synchronization ensures you're running the latest secure version
- Regular security audits and updates

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