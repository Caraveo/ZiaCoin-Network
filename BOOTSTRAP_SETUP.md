# ZiaCoin Network Bootstrap Node Setup

This guide explains how to set up and run your IP `216.255.208.105` as the first bootstrap node in the ZiaCoin Network.

## 🌟 What is a Bootstrap Node?

A bootstrap node is the **first node** in a peer-to-peer network that other nodes connect to when joining the network. It serves as the initial point of contact for:

- **Node Discovery**: Other nodes find the network through bootstrap nodes
- **Blockchain Sync**: New nodes download the current blockchain state
- **Peer Introduction**: Bootstrap nodes introduce new nodes to other peers
- **Network Stability**: Provides a reliable entry point to the network

## 🚀 Quick Start

### 1. Start the Bootstrap Node

```bash
# Make the script executable (if not already done)
chmod +x start_bootstrap.sh

# Start the bootstrap node
./start_bootstrap.sh
```

### 2. Verify the Node is Running

```bash
# Test the bootstrap node
python3 test_bootstrap.py
```

### 3. Check Node Status

Visit these URLs in your browser:
- **Node Status**: http://216.255.208.105:9999/status
- **Blockchain**: http://216.255.208.105:9999/chain
- **API Documentation**: See below

## 📋 API Endpoints

Your bootstrap node exposes these HTTP endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Get node status and health |
| `/chain` | GET | Get the full blockchain |
| `/balance/{address}` | GET | Get wallet balance |
| `/transaction` | POST | Create a new transaction |
| `/wallet/new` | POST | Create a new wallet |
| `/mine` | POST | Mine a new block |

## 🔧 Configuration

The bootstrap node is configured in `node.conf`:

```json
{
    "node": {
        "host": "216.255.208.105",
        "port": 9999,
        "peers": ["216.255.208.105:9999"],
        "max_peers": 10,
        "sync_interval": 300
    }
}
```

## 🌐 Network Architecture

### Peer Discovery Flow

1. **New Node Joins**: A new node wants to join the network
2. **Bootstrap Connection**: New node connects to your bootstrap node (`216.255.208.105:9999`)
3. **Handshake**: Nodes exchange version and capability information
4. **Peer Exchange**: Bootstrap node shares list of known peers
5. **Blockchain Sync**: New node downloads current blockchain state
6. **Network Integration**: New node connects to other peers and becomes part of the network

### DHT (Distributed Hash Table)

The network uses a Kademlia DHT for efficient peer discovery:

- **Routing Table**: Maintains k-buckets for efficient node lookup
- **Peer Store**: Stores peer information for quick access
- **Node Maintenance**: Automatically removes inactive nodes

## 🔒 Security Features

Your bootstrap node includes:

- **Rate Limiting**: Prevents abuse with request limits
- **Connection Limits**: Maximum 100 concurrent connections
- **Timeout Handling**: Automatic cleanup of stale connections
- **Input Validation**: All API inputs are validated
- **Error Handling**: Graceful error responses

## 📊 Monitoring

### Health Checks

The node performs automatic health checks every 60 seconds:

- **Blockchain Validation**: Verifies chain integrity
- **Peer Connectivity**: Checks peer connections
- **Storage Health**: Validates wallet storage
- **System Resources**: Monitors memory and CPU usage

### Logs

Logs are written to:
- **Console**: Real-time colored output
- **File**: `node.log` with rotation
- **Level**: INFO and above

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 9999
   lsof -i :9999
   
   # Kill the process or change port
   python3 node.py --port 9998
   ```

2. **Firewall Issues**
   ```bash
   # Ensure port 9999 is open
   sudo ufw allow 9999
   ```

3. **Node Won't Start**
   ```bash
   # Check dependencies
   pip3 install -r requirements.txt
   
   # Check Python version
   python3 --version  # Should be 3.8+
   ```

### Debug Mode

For troubleshooting, run with debug logging:

```bash
# Set debug level
export ZIACOIN_LOG_LEVEL=DEBUG

# Start node
python3 node.py --bootstrap
```

## 🔗 Connecting Other Nodes

Other nodes can connect to your bootstrap node by:

1. **Using your IP in their config**:
   ```json
   {
       "node": {
           "peers": ["216.255.208.105:9999"]
       }
   }
   ```

2. **Command line**:
   ```bash
   python3 node.py --bootstrap-nodes "216.255.208.105:9999"
   ```

## 📈 Performance

### Recommended System Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB+
- **Storage**: 10GB+ (for blockchain growth)
- **Network**: 10Mbps+ upload

### Optimization Tips

1. **SSD Storage**: Use SSD for faster blockchain access
2. **Dedicated IP**: Ensure your IP is stable and accessible
3. **Regular Backups**: Backup the `chain/` directory regularly
4. **Monitor Resources**: Watch CPU and memory usage

## 🎯 Next Steps

Once your bootstrap node is running:

1. **Test Connectivity**: Use `test_bootstrap.py` to verify
2. **Create Wallets**: Use the wallet API to create test wallets
3. **Mine Blocks**: Start mining to grow the blockchain
4. **Invite Peers**: Share your IP with other network participants
5. **Monitor Growth**: Watch the network expand

## 📞 Support

If you encounter issues:

1. Check the logs in `node.log`
2. Run the test script: `python3 test_bootstrap.py`
3. Verify network connectivity: `ping 216.255.208.105`
4. Check firewall settings

---

**Your bootstrap node is the foundation of the ZiaCoin Network!** 🌟 