#!/usr/bin/env python3
"""
MySQL setup script for Job Automation Application.
"""
import os
import sys
import subprocess
from loguru import logger

def check_mysql_installed():
    """Check if MySQL is installed and accessible."""
    try:
        result = subprocess.run(['mysql', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.success(f"MySQL found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("MySQL not found. Please install MySQL first.")
        return False

def create_database():
    """Create the job_automation database."""
    try:
        # Get database details from user
        host = input("MySQL host [localhost]: ").strip() or "localhost"
        port = input("MySQL port [3306]: ").strip() or "3306"
        root_user = input("MySQL root username [root]: ").strip() or "root"
        root_password = input("MySQL root password: ").strip()
        
        # Create database
        create_db_sql = f"""
        CREATE DATABASE IF NOT EXISTS job_automation 
        CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """
        
        cmd = ['mysql', '-h', host, '-P', port, '-u', root_user, f'-p{root_password}', '-e', create_db_sql]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.success("Database 'job_automation' created successfully")
        
        return host, port, root_user, root_password
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create database: {e}")
        return None, None, None, None

def create_user(host, port, root_user, root_password):
    """Create a dedicated user for the application."""
    try:
        username = input("Application username [job_user]: ").strip() or "job_user"
        password = input("Application password: ").strip()
        
        create_user_sql = f"""
        CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY '{password}';
        GRANT ALL PRIVILEGES ON job_automation.* TO '{username}'@'localhost';
        FLUSH PRIVILEGES;
        """
        
        cmd = ['mysql', '-h', host, '-P', port, '-u', root_user, f'-p{root_password}', '-e', create_user_sql]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.success(f"User '{username}' created successfully")
        
        return username, password
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create user: {e}")
        return None, None

def update_config(host, port, username, password):
    """Update config.yaml with MySQL settings."""
    try:
        config_content = f"""# Database Configuration
database:
  type: "mysql"  # Changed from sqlite to mysql
  sqlite_path: "./job_automation.db"
  mysql:
    host: "{host}"
    port: {port}
    database: "job_automation"
    username: "{username}"
    password: "{password}"
    charset: "utf8mb4"
"""
        
        # Update config.yaml
        with open('config.yaml', 'r') as f:
            content = f.read()
        
        # Replace database section
        import re
        pattern = r'# Database Configuration\ndatabase:.*?(?=\n# |$)'
        replacement = config_content.rstrip()
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            # Add at the end if not found
            new_content = content + '\n' + config_content
        
        with open('config.yaml', 'w') as f:
            f.write(new_content)
        
        logger.success("config.yaml updated with MySQL settings")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("🚀 MySQL Setup for Job Automation Application")
    logger.info("=" * 50)
    
    # Check MySQL installation
    if not check_mysql_installed():
        sys.exit(1)
    
    # Create database
    host, port, root_user, root_password = create_database()
    if not host:
        sys.exit(1)
    
    # Create user
    username, password = create_user(host, port, root_user, root_password)
    if not username:
        sys.exit(1)
    
    # Update configuration
    if update_config(host, port, username, password):
        logger.success("✅ MySQL setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Install MySQL client: pip install mysqlclient")
        logger.info("2. Test connection: python test_system.py")
        logger.info("3. Initialize database: python cli.py init")
    else:
        logger.error("❌ MySQL setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

