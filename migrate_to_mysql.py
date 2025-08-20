#!/usr/bin/env python3
"""
Migration script to switch from SQLite to MySQL.
"""
import os
import sys
import sqlite3
import yaml
from loguru import logger

def load_config():
    """Load current configuration."""
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

def check_sqlite_data():
    """Check if SQLite database has data."""
    if not os.path.exists('job_automation.db'):
        logger.warning("SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect('job_automation.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("No tables found in SQLite database")
            return False
        
        # Check data in each table
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            logger.info(f"Table {table_name}: {count} records")
        
        conn.close()
        
        if total_records == 0:
            logger.warning("No data found in SQLite database")
            return False
        
        logger.success(f"Found {total_records} total records in SQLite database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to check SQLite data: {e}")
        return False

def backup_sqlite():
    """Create a backup of the SQLite database."""
    try:
        if os.path.exists('job_automation.db'):
            import shutil
            backup_name = f"job_automation_backup_{int(time.time())}.db"
            shutil.copy2('job_automation.db', backup_name)
            logger.success(f"SQLite database backed up as {backup_name}")
            return backup_name
        return None
    except Exception as e:
        logger.error(f"Failed to backup SQLite database: {e}")
        return None

def update_config_to_mysql():
    """Update config.yaml to use MySQL."""
    try:
        config = load_config()
        if not config:
            return False
        
        # Get MySQL details from user
        host = input("MySQL host [localhost]: ").strip() or "localhost"
        port = input("MySQL port [3306]: ").strip() or "3306"
        username = input("MySQL username: ").strip()
        password = input("MySQL password: ").strip()
        database = input("MySQL database [job_automation]: ").strip() or "job_automation"
        
        # Update database configuration
        config['database'] = {
            'type': 'mysql',
            'sqlite_path': './job_automation.db',
            'mysql': {
                'host': host,
                'port': int(port),
                'database': database,
                'username': username,
                'password': password,
                'charset': 'utf8mb4'
            }
        }
        
        # Save updated config
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.success("Configuration updated to use MySQL")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("🔄 SQLite to MySQL Migration")
    logger.info("=" * 40)
    
    # Check current configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    current_db_type = config.get('database', {}).get('type', 'sqlite')
    if current_db_type == 'mysql':
        logger.info("✅ Already using MySQL")
        return
    
    logger.info(f"Current database type: {current_db_type}")
    
    # Check if there's data to migrate
    has_data = check_sqlite_data()
    
    if has_data:
        logger.info("📊 Data found in SQLite database")
        backup = backup_sqlite()
        if backup:
            logger.info(f"Backup created: {backup}")
        
        response = input("Do you want to migrate the data to MySQL? (y/N): ").strip().lower()
        if response == 'y':
            logger.info("⚠️  Data migration not implemented yet")
            logger.info("Please manually migrate data or start fresh with MySQL")
    
    # Update configuration
    logger.info("Updating configuration to use MySQL...")
    if update_config_to_mysql():
        logger.success("✅ Migration completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Ensure MySQL is running and accessible")
        logger.info("2. Install MySQL client: pip install mysqlclient")
        logger.info("3. Test connection: python test_system.py")
        logger.info("4. Initialize MySQL database: python cli.py init")
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    import time
    main()

