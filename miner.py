#!/usr/bin/env python3
import sys
import os

# Add the modules directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import the sync module
from sync.sync import CodeSync

def check_sync():
    """Check if code is synchronized with remote repository."""
    sync = CodeSync()
    if not sync.sync():
        print("Code synchronization failed. Please update your code.")
        sys.exit(1)

# Check code synchronization before proceeding
check_sync()

# ... existing code ... 