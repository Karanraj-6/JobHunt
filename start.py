#!/usr/bin/env python3
"""
Simple startup script for the Job Automation Application.
"""
import os
import sys
from loguru import logger

def main():
    """Main startup function."""
    print("🚀 Job Automation Application")
    print("=" * 40)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected")
        print("   It's recommended to activate a virtual environment first")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("   Please create a .env file with your API keys and credentials")
        print("   cp env.template .env")
        print("   # Then edit .env with your actual values")
        print()
    
    # Check if config.yaml exists
    if not os.path.exists('config.yaml'):
        print("❌ Error: config.yaml not found")
        print("   This file is required for the application to run")
        return 1
    
    # Check if database is initialized
    if not os.path.exists('job_automation.db'):
        print("ℹ️  Database not initialized yet")
        print("   Run: python cli.py init")
        print()
    
    print("📋 Available commands:")
    print("   python cli.py init          # Initialize database")
    print("   python cli.py status        # Check system status")
    print("   python cli.py fetch         # Manually fetch jobs")
    print("   python cli.py post          # Manually post content")
    print("   python cli.py start         # Start automated mode")
    print("   python test_system.py       # Run system tests")
    print("   python test_gemini.py       # Test Gemini API integration")
    print("   python setup_mysql.py       # Setup MySQL database")
    print("   python migrate_to_mysql.py  # Migrate from SQLite to MySQL")
    print()
    
    print("🔧 Quick start:")
    print("   1. python cli.py init       # Initialize database")
    print("   2. python cli.py status     # Verify system status")
    print("   3. python cli.py start      # Start automation")
    print()
    
    print("📚 For more information, see README.md")
    print("=" * 40)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
