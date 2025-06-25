#!/usr/bin/env python3
"""
Production Startup Script for ZiaCoin Network
Uses Gunicorn WSGI server instead of Flask development server
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def start_production_server(host='0.0.0.0', port=5000, workers=4):
    """Start the production server using Gunicorn."""
    
    # Check if Gunicorn is installed
    try:
        import gunicorn
    except ImportError:
        print("❌ Gunicorn not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn"], check=True)
    
    # Gunicorn configuration
    gunicorn_config = {
        'bind': f'{host}:{port}',
        'workers': workers,
        'worker_class': 'sync',
        'worker_connections': 1000,
        'max_requests': 1000,
        'max_requests_jitter': 50,
        'timeout': 30,
        'keepalive': 2,
        'preload_app': True,
        'access_logfile': '-',
        'error_logfile': '-',
        'loglevel': 'info'
    }
    
    # Build gunicorn command
    cmd = [
        'gunicorn',
        '--bind', gunicorn_config['bind'],
        '--workers', str(gunicorn_config['workers']),
        '--worker-class', gunicorn_config['worker_class'],
        '--worker-connections', str(gunicorn_config['worker_connections']),
        '--max-requests', str(gunicorn_config['max_requests']),
        '--max-requests-jitter', str(gunicorn_config['max_requests_jitter']),
        '--timeout', str(gunicorn_config['timeout']),
        '--keepalive', str(gunicorn_config['keepalive']),
        '--preload',
        '--access-logfile', gunicorn_config['access_logfile'],
        '--error-logfile', gunicorn_config['error_logfile'],
        '--log-level', gunicorn_config['loglevel'],
        'app:app'  # app.py:app Flask application
    ]
    
    print(f"🚀 Starting ZiaCoin Network in PRODUCTION mode")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Server: Gunicorn")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Production server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start production server: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Start ZiaCoin Network in Production Mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker processes (default: 4)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (1024 <= args.port <= 65535):
        print("❌ Port must be between 1024 and 65535")
        sys.exit(1)
    
    if args.workers < 1:
        print("❌ Number of workers must be at least 1")
        sys.exit(1)
    
    start_production_server(args.host, args.port, args.workers)

if __name__ == "__main__":
    main() 