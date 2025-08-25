#!/usr/bin/env python3
"""
Production Deployment Script for Job Automation System
This is the main entry point for running the automation in production.
"""

import os
import sys
import signal
import time
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup production logging."""
    # Remove default logger
    logger.remove()
    
    # Add console logger with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Add file logger for production
    logger.add(
        "logs/automation.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )

def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    if not os.path.exists("logs"):
        os.makedirs("logs")
        logger.info("Created logs directory")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main production entry point."""
    # Load environment variables
    load_dotenv()
    
    # Create logs directory
    create_logs_directory()
    
    # Setup logging
    setup_logging()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("🚀 JOB AUTOMATION SYSTEM - PRODUCTION DEPLOYMENT")
    logger.info("=" * 60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    try:
        # Import orchestrator
        from orchestrator import JobAutomationOrchestrator
        
        logger.info("✅ All modules imported successfully")
        
        # Initialize orchestrator
        logger.info("🔧 Initializing Job Automation Orchestrator...")
        orchestrator = JobAutomationOrchestrator('config.yaml')
        
        logger.info("✅ Orchestrator initialized successfully")
        logger.info("🚀 Starting automation system...")
        logger.info("📋 System will:")
        logger.info("   • Fetch jobs from RapidAPI and Jooble")
        logger.info("   • Filter for entry-level positions (0-2 years)")
        logger.info("   • Generate captions with proper formatting")
        logger.info("   • Post to LinkedIn automatically")
        logger.info("   • Handle daily posting limits")
        logger.info("   • Run continuously until stopped")
        logger.info("")
        logger.info("💡 To stop the system, press Ctrl+C")
        logger.info("=" * 60)
        
        # Start the orchestrator
        orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
        try:
            orchestrator.stop()
            logger.info("✅ Orchestrator stopped gracefully")
        except:
            pass
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error("Stack trace:", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("=" * 60)
        logger.info("👋 Job Automation System stopped")
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()

