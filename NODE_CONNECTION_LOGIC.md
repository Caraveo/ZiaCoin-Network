# ZiaCoin Node Connection Logic

## Overview

The ZiaCoin network implements a strict connection hierarchy to ensure all nodes are connected to the main network through the initial bootstrap node.

## Node Types

### 1. Initial Node (216.255.208.105:9999)
- **Command**: `python node.py --init`
- **Purpose**: The main network entry point
- **Behavior**: 
  - Starts as the primary bootstrap node
  - Other nodes connect to this node
  - Does not require connection validation to itself
  - External access: `http://216.255.208.105:9999`

### 2. Regular Nodes
- **Command**: `python node.py`
- **Purpose**: Standard network participants
- **Behavior**:
  - **MUST** connect to initial node (216.255.208.105:9999) first
  - **FAILS** if initial node is unreachable
  - Cannot start without network connection
  - Automatically adds initial node as first peer

### 3. Bootstrap Nodes
- **Command**: `python node.py --bootstrap`
- **Purpose**: Additional bootstrap nodes for redundancy
- **Behavior**:
  - Starts as secondary bootstrap node
  - Adds initial node as first peer
  - Provides additional network entry points

## Connection Validation

### Regular Node Startup Process
1. **Pre-validation**: Attempts to connect to `216.255.208.105:9999`
2. **Success**: Node starts normally with initial node as peer
3. **Failure**: Node exits with error message

### Error Handling
- **Connection Error**: "Cannot start node without connection to initial node"
- **Timeout**: "Timeout connecting to initial node"
- **Invalid Response**: "Initial node returned status [code]"

## Usage Examples

### Start Initial Node
```bash
# Start the main network entry point
python node.py --init

# Output:
# ✓ Starting as INITIAL bootstrap node on 0.0.0.0:9999
# ℹ External access: http://216.255.208.105:9999
# ℹ This is the main network entry point
```

### Start Regular Node
```bash
# Start a regular node (requires initial node to be running)
python node.py

# Output:
# ℹ Regular node mode - attempting to connect to initial node...
# ✓ Connected to initial node: 216.255.208.105:9999
# ✓ Node started successfully
```

### Start Regular Node on Different Port
```bash
# Start regular node on port 9998
python node.py --port 9998

# Output:
# ℹ Regular node mode - attempting to connect to initial node...
# ✓ Connected to initial node: 216.255.208.105:9999
# ✓ Node started successfully
# ℹ Listening on 0.0.0.0:9998
```

### Start Bootstrap Node
```bash
# Start additional bootstrap node
python node.py --bootstrap --port 9997

# Output:
# ✓ Starting as bootstrap node on 0.0.0.0:9997
# ℹ External access: http://216.255.208.105:9999
```

## Network Architecture

```
                    ┌─────────────────┐
                    │   Initial Node  │
                    │ 216.255.208.105 │
                    │     :9999       │
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │                 │
            ┌───────▼──────┐  ┌───────▼──────┐
            │ Regular Node │  │ Regular Node │
            │   :9998      │  │   :9999      │
            └──────────────┘  └──────────────┘
```

## Testing

Run the connection logic test:
```bash
python test_node_connection.py
```

This will validate:
- Initial node connectivity
- Regular node startup logic
- Initial node startup logic

## Security Benefits

1. **Network Integrity**: All nodes must connect to the main network
2. **Prevents Isolation**: Nodes cannot start in isolation
3. **Centralized Control**: Network entry point is controlled
4. **Fail-Fast**: Nodes fail quickly if network is unreachable

## Configuration

The connection logic is implemented in:
- `node.py`: Main node startup and argument parsing
- `modules/network/peer.py`: Peer network connection validation

## Troubleshooting

### Node Won't Start
1. Check if initial node (216.255.208.105:9999) is running
2. Verify network connectivity to the initial node
3. Check firewall settings
4. Ensure port 9999 is not blocked

### Connection Timeout
1. Initial node may be overloaded
2. Network latency issues
3. DNS resolution problems
4. Firewall blocking connections

### Port Already in Use
1. Use `--port` flag to specify different port
2. Check what's using the port: `lsof -i :9999`
3. Stop conflicting services 