"""
Database initialization and connection management.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from models import Base
import yaml

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize database manager with configuration."""
        self.config_path = config_path
        self.engine = None
        self.SessionLocal = None
        self.config = self._load_config()
        self._setup_database()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _setup_database(self):
        """Setup database connection based on configuration."""
        db_config = self.config.get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            db_path = db_config.get('sqlite_path', './job_automation.db')
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            database_url = f"sqlite:///{db_path}"
            logger.info(f"Using SQLite database: {db_path}")
        
        elif db_type == 'mysql':
            mysql_config = db_config.get('mysql', {})
            host = mysql_config.get('host', 'localhost')
            port = mysql_config.get('port', 3306)
            database = mysql_config.get('database', 'job_automation')
            username = mysql_config.get('username', 'username')
            password = mysql_config.get('password', 'password')
            charset = mysql_config.get('charset', 'utf8mb4')
            
            database_url = f"mysql://{username}:{password}@{host}:{port}/{database}?charset={charset}"
            logger.info(f"Using MySQL database: {host}:{port}/{database}")
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        try:
            self.engine = create_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.success("Database connection established successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.success("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = None

def init_database(config_path: str = "config.yaml") -> DatabaseManager:
    """Initialize the global database manager."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(config_path)
    return db_manager

def get_db() -> Session:
    """Get a database session."""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager.get_session()

def close_database():
    """Close the global database manager."""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None
