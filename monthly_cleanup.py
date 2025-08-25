#!/usr/bin/env python3
"""
Monthly MongoDB cleanup script for Job Automation System.
Clears all collections to prevent storage bloat and ensure fresh data.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import config

def main():
    """Main cleanup function."""
    load_dotenv()
    
    logger.info("Starting monthly MongoDB cleanup...")
    
    try:
        # Initialize database connection
        db = DatabaseManager(config)
        
        # Get all collections
        collections = [
            'raw_jobs',
            'clean_jobs', 
            'posts_ready',
            'posted_items'
        ]
        
        total_deleted = 0
        
        for collection_name in collections:
            try:
                collection = db.get_collection(collection_name)
                
                # Count documents before deletion
                count_before = collection.count_documents({})
                
                # Delete all documents in the collection
                result = collection.delete_many({})
                
                total_deleted += result.deleted_count
                
                logger.info(f"Cleared {collection_name}: {count_before} documents deleted")
                
            except Exception as e:
                logger.error(f"Error clearing {collection_name}: {e}")
                continue
        
        # Close database connection
        db.close()
        
        logger.success(f"Monthly cleanup completed! Total documents deleted: {total_deleted}")
        
        # Create a cleanup log entry
        cleanup_log = {
            'timestamp': datetime.utcnow(),
            'action': 'monthly_cleanup',
            'documents_deleted': total_deleted,
            'collections_cleared': collections
        }
        
        # Store cleanup log in a separate collection
        db = DatabaseManager(config)
        cleanup_collection = db.get_collection('cleanup_logs')
        cleanup_collection.insert_one(cleanup_log)
        db.close()
        
        logger.info("Cleanup log stored successfully")
        
    except Exception as e:
        logger.error(f"Monthly cleanup failed: {e}")
        sys.exit(1)

def check_last_cleanup():
    """Check when the last cleanup was performed."""
    load_dotenv()
    
    try:
        db = DatabaseManager(config)
        cleanup_collection = db.get_collection('cleanup_logs')
        
        # Get the most recent cleanup
        last_cleanup = cleanup_collection.find_one(
            {'action': 'monthly_cleanup'},
            sort=[('timestamp', -1)]
        )
        
        if last_cleanup:
            last_date = last_cleanup['timestamp']
            days_since = (datetime.utcnow() - last_date).days
            logger.info(f"Last cleanup: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Days since last cleanup: {days_since}")
            
            if days_since >= 30:
                logger.warning("It's been more than 30 days since last cleanup!")
                return True
            else:
                logger.info("Cleanup not needed yet")
                return False
        else:
            logger.info("No previous cleanup found")
            return True
            
    except Exception as e:
        logger.error(f"Error checking last cleanup: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Check if cleanup is needed
    if check_last_cleanup():
        logger.info("Proceeding with monthly cleanup...")
        main()
    else:
        logger.info("Cleanup not needed yet. Use --force to override.")
        
        # Allow force cleanup with --force flag
        if len(sys.argv) > 1 and sys.argv[1] == "--force":
            logger.warning("Force cleanup requested...")
            main()

