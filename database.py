"""
Database initialization and connection management (MongoDB).
"""
import os
from typing import Optional
from loguru import logger
import yaml
from pymongo import MongoClient
from pymongo.collection import Collection

class DatabaseManager:
    """Manages MongoDB connections and collections."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.client: Optional[MongoClient] = None
        self.db = None
        self.config = self._load_config()
        self._setup_database()

    def _load_config(self) -> dict:
        try:
            # Use config.py which loads from config.yaml and injects env vars
            from config import config
            return config
        except ImportError as e:
            logger.error(f"Error importing config.py: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def _setup_database(self):
        db_config = self.config.get('database', {})
        db_type = db_config.get('type', 'mongodb')
        if db_type != 'mongodb':
            logger.warning(f"Database type '{db_type}' specified, overriding to 'mongodb'")
        mongo_cfg = db_config.get('mongodb', {})
        uri = mongo_cfg.get('uri', os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
        database_name = mongo_cfg.get('database', os.getenv('MONGODB_DB', 'job_automation'))
        try:
            # Configure MongoDB client with SSL options for Atlas
            client_options = {
                'serverSelectionTimeoutMS': 10000,
                'connectTimeoutMS': 10000,
                'socketTimeoutMS': 10000,
                'retryWrites': True,
                'w': 'majority'
            }
            
            # Add SSL configuration for Atlas connections
            if 'mongodb+srv://' in uri or 'ssl=true' in uri:
                client_options.update({
                    'tls': True,
                    'tlsInsecure': True  # This bypasses all SSL certificate validation
                })
                logger.warning("Using insecure SSL settings for MongoDB Atlas connection")
            
            self.client = MongoClient(uri, **client_options)
            # Trigger server selection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            logger.success(f"Connected to MongoDB at {uri[:50]}..., db={database_name}")
            # Ensure common indexes
            self._ensure_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _ensure_indexes(self):
        try:
            # jobs_clean unique key on source+source_job_id or apply_url
            self.get_collection('jobs_clean').create_index(
                [('source', 1), ('source_job_id', 1)], unique=False
            )
            self.get_collection('jobs_clean').create_index(
                [('apply_url', 1)], unique=False
            )
            # posts_ready indexes
            self.get_collection('posts_ready').create_index([('status', 1)])
            self.get_collection('posts_ready').create_index([('platform', 1)])
            self.get_collection('posts_ready').create_index([('scheduled_for', 1)])
            # posted_items index
            self.get_collection('posted_items').create_index([('platform', 1)])
            self.get_collection('posted_items').create_index([('posted_at', 1)])
        except Exception as e:
            logger.warning(f"Failed to ensure indexes: {e}")

    def get_collection(self, name: str) -> Collection:
        if self.db is None:
            raise RuntimeError('MongoDB not initialized')
        return self.db[name]

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def init_database(config_path: str = "config.yaml") -> DatabaseManager:
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(config_path)
    return db_manager

def get_db() -> DatabaseManager:
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager

def close_database():
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None
