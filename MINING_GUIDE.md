# 🛠️ ZiaCoin Network Mining Guide

Learn how to start mining ZIA coins and earn rewards in the ZiaCoin Network!

## 🚀 Quick Start Mining

### **Method 1: Node-Based Mining (Recommended)**

```bash
# 1. Start your bootstrap node
./start_bootstrap.sh

# 2. In another terminal, start mining
python3 start_mining.py
```

### **Method 2: Standalone Mining**

```bash
# Mine without connecting to a node
python3 start_mining.py --standalone
```

### **Method 3: API Mining**

```bash
# Start node first, then trigger mining via API
curl -X POST http://localhost:9999/mine
```

## 📊 Mining Options

### **Basic Mining**
```bash
# Connect to local node
python3 start_mining.py

# Connect to specific node
python3 start_mining.py --node http://216.255.208.105:9999
```

### **Standalone Mining**
```bash
# Mine independently (creates local blockchain)
python3 start_mining.py --standalone
```

### **Check Status**
```bash
# Check mining/node status
python3 start_mining.py --status
```

## 💰 Mining Rewards

- **Block Reward**: 50 ZIA per block
- **Difficulty**: Adjusts automatically based on network hash rate
- **Block Time**: Target ~60 seconds between blocks
- **Transaction Fees**: Additional rewards from transaction fees

## 🔧 Mining Configuration

### **Difficulty Settings**
- **Starting Difficulty**: 4 (4 leading zeros required)
- **Auto-Adjustment**: Based on block time
- **Target Block Time**: 60 seconds

### **Mining Parameters**
```json
{
    "difficulty": 4,
    "mining_reward": 50,
    "block_time": 60,
    "max_block_size": 1048576
}
```

## 🏗️ How Mining Works

### **Proof of Work (PoW)**
1. **Block Creation**: New block with pending transactions
2. **Nonce Increment**: Try different nonce values
3. **Hash Calculation**: SHA-256 hash of block data
4. **Difficulty Check**: Hash must start with required zeros
5. **Block Found**: Valid hash found, block added to chain
6. **Reward**: 50 ZIA sent to miner's address

### **Mining Process**
```
Block Data → Hash Function → Check Difficulty → Valid? → Add to Chain
     ↓              ↓              ↓              ↓         ↓
Transactions   SHA-256      Leading Zeros    Yes/No    Reward
```

## 📈 Mining Statistics

### **Real-time Monitoring**
```bash
# Check mining status
python3 start_mining.py --status

# Monitor node
curl http://localhost:9999/status
```

### **Blockchain Info**
```bash
# View blockchain
curl http://localhost:9999/chain

# Check balance
curl http://localhost:9999/balance/{address}
```

## 🔒 Security Features

### **Mining Security**
- **Transaction Verification**: All transactions verified before mining
- **Block Validation**: Blocks validated by network consensus
- **Double Spending Protection**: Prevents duplicate transactions
- **Chain Integrity**: Cryptographic linking prevents tampering

### **Wallet Security**
- **Encrypted Storage**: Private keys encrypted with AES-GCM
- **Mnemonic Recovery**: 12-word phrase for wallet recovery
- **Secure Signing**: ECDSA signatures for transactions

## 🛠️ Troubleshooting

### **Common Issues**

1. **"Node not responding"**
   ```bash
   # Check if node is running
   python3 test_local.py
   
   # Start node if needed
   ./start_bootstrap.sh
   ```

2. **"No pending transactions"**
   ```bash
   # Create some transactions first
   curl -X POST http://localhost:9999/wallet/new
   curl -X POST http://localhost:9999/transaction \
     -H "Content-Type: application/json" \
     -d '{"sender":"address1","recipient":"address2","amount":10}'
   ```

3. **"Mining too slow"**
   - Difficulty may be too high
   - Check system resources
   - Consider running standalone mode

### **Performance Tips**

1. **Use SSD Storage**: Faster blockchain access
2. **Adequate RAM**: 4GB+ recommended
3. **Stable Network**: Reliable internet connection
4. **Regular Backups**: Backup wallet and chain data

## 🌐 Network Mining

### **Joining the Network**
```bash
# Connect to bootstrap node
python3 start_mining.py --node http://216.255.208.105:9999

# Or use your own node
python3 node.py --bootstrap
python3 start_mining.py
```

### **Mining Pool (Future)**
- Pool mining for consistent rewards
- Shared difficulty and rewards
- Better for smaller miners

## 📱 Mining Commands Reference

| Command | Description |
|---------|-------------|
| `python3 start_mining.py` | Start mining on local node |
| `python3 start_mining.py --standalone` | Standalone mining |
| `python3 start_mining.py --status` | Check status |
| `python3 start_mining.py --node URL` | Connect to specific node |
| `curl -X POST localhost:9999/mine` | Trigger mining via API |

## 🎯 Next Steps

1. **Start Mining**: Use one of the methods above
2. **Monitor Progress**: Check status regularly
3. **Create Wallets**: Store your mining rewards
4. **Join Network**: Connect with other miners
5. **Optimize**: Fine-tune your mining setup

---

**Happy Mining! 🚀💰** 