#!/usr/bin/env python3
"""
Startup script for Zillow Property Manager Web Application
"""
import os
import sys
import socket
import subprocess
from pathlib import Path

def find_free_port(start_port=5000, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ['flask', 'sqlalchemy', 'pandas', 'twilio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_config_files():
    """Check if required configuration files exist"""
    config_files = ['search_configs.json', 'twilio_config.json']
    missing_files = []
    
    for file in config_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Missing configuration files: {', '.join(missing_files)}")
        print("The application will still run, but some features may not work properly.")
        return False
    
    print("✅ Configuration files found")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Zillow Property Manager Web Application")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check config files
    check_config_files()
    
    # Find free port
    port = find_free_port(5000)
    if not port:
        print("❌ Could not find a free port")
        sys.exit(1)
    
    print(f"🌐 Web application will be available at: http://localhost:{port}")
    print("=" * 60)
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Start the Flask application
    try:
        from app import app
        print("✅ Flask application loaded successfully")
        print("🔄 Starting web server...")
        print("📝 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=port)
        
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
