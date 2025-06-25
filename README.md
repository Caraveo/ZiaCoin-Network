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

## 🌟 Light Wallet Implementation

The ZiaCoin Network features a **Light Wallet** system designed for fast, efficient blockchain interactions. Light wallets are optimized for quick transactions and mobile-first designs, providing a streamlined experience without the overhead of full node synchronization.

### How Light Wallets Work

#### **Dual Connection Modes**

1. **Direct Local Connection** (Default)
   - Connects directly to the node backend on the same machine
   - Uses direct function calls - no HTTP overhead
   - Optimal performance for local operations
   - Bypasses network layer for enhanced security

2. **Remote HTTP Connection**
   - Connects via HTTP API to remote nodes
   - Works with any remote API server
   - Suitable for mobile apps and web interfaces
   - Enables cross-platform wallet access

#### **Connection Logic**

```bash
# Local direct connection (fastest)
python wallet.py balance <address>
# → Connects directly to node backend (localhost:9999)
# → Uses direct function calls - no HTTP overhead

# Remote HTTP connection
python wallet.py --node localhost:8000 balance <address>
python wallet.py --node 216.255.208.105:8000 balance <address>
# → Connects via HTTP API
# → Works with any remote API server running node service
```

#### **Key Benefits**

- **⚡ Performance**: Direct connections are faster (no HTTP overhead)
- **🔒 Security**: Local connections bypass network layer
- **📱 Mobile-Friendly**: HTTP API enables mobile app integration
- **🔄 Flexibility**: Easy switching between local and remote
- **🛡️ Reliability**: Automatic fallback and error handling

#### **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Light Wallet  │    │   Node Backend  │    │   API Server    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Direct      │◄┼────┼►│ Blockchain  │◄┼────┼►│ HTTP API    │ │
│ │ Interface   │ │    │ │ Components  │ │    │ │ Endpoints   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ |
└────────|────────┘    └─────────────────┘    └────────│────────┘
         |                                             │
         |                                             │
         |                                             │
┌────────|────────┐    ┌─────────────────┐    ┌────────|────────┐                 
│ ┌─────────────┐ │    | ┌─────────────┐ |    │ ┌─────────────┐ │
│ │ HTTP        │◄┼────┼►│ Wallet      │◄┼────┼►│ Proxy to    │ │
│ │ Interface   │ │    │ │ Manager     │ │    │ │ Backend     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### **Usage Examples**

```bash
# Check wallet balance (local)
python wallet.py balance <wallet_address>

# List all wallets (local)
python wallet.py list

# Send transaction (local)
python wallet.py send <from_address> <to_address> <amount> <passphrase>

# Remote operations
python wallet.py --node localhost:8000 balance <address>
python wallet.py --node 216.255.208.105:8000 send <from> <to> <amount> <pass>
```

#### **Mobile Integration**

The Light Wallet's HTTP API enables easy integration with mobile applications:

```javascript
// Example mobile app API call
const response = await fetch('http://node-address:8000/balance/wallet-address');
const balance = await response.json();
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ZiaCoin-Network.git
cd ZiaCoin-Network
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the node backend:
```bash
python node.py --init
```

4. Start the API server (optional, for remote access):
```bash
python node.py --api
```

5. Use the Light Wallet:
```bash
# Local operations
python wallet.py balance <address>

# Remote operations
python wallet.py --node localhost:8000 balance <address>
```

## Configuration

### Node Configuration (`node.conf`)

```json
{
    "node": {
        "host": "localhost",
        "port": 9999,
        "peers": []
    },
    "blockchain": {
        "difficulty": 4,
        "mining_reward": 50,
        "block_time": 60
    }
}
```

### Wallet Configuration (`wallet.conf`)

```json
{
    "node": {
        "host": "localhost",
        "port": 9999
    },
    "wallet": {
        "storage_path": "chain/wallets/"
    }
}
```

## API Endpoints

When using the API server (`python node.py --api`), the following endpoints are available:

- `GET /status` - Node status and peer count
- `GET /peers` - Connected peers list
- `GET /network` - Detailed network information
- `GET /chain` - Full blockchain
- `GET /balance/{address}` - Wallet balance
- `POST /transaction` - Create new transaction
- `GET /health` - Health check

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 