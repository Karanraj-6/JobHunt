# MySQL Migration Guide

This guide will help you migrate your Job Automation Application from PostgreSQL/SQLite to MySQL.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the MySQL setup script
python setup_mysql.py

# Or on Windows
setup_mysql.bat
```

### Option 2: Manual Setup
```bash
# 1. Install MySQL client
pip install mysqlclient

# 2. Create database and user manually
mysql -u root -p
CREATE DATABASE job_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'job_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON job_automation.* TO 'job_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 3. Update config.yaml
# 4. Test connection
python test_system.py
```

## 📋 Prerequisites

- MySQL 8.0+ installed and running
- Python 3.10+
- Access to MySQL root account (for initial setup)

## 🔧 Installation Steps

### 1. Install MySQL Server

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### CentOS/RHEL
```bash
sudo yum install mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld
```

#### Windows
Download and install from: https://dev.mysql.com/downloads/mysql/

#### macOS
```bash
brew install mysql
brew services start mysql
```

### 2. Install Python MySQL Client
```bash
pip install mysqlclient
```

### 3. Secure MySQL Installation
```bash
sudo mysql_secure_installation
```

## ⚙️ Configuration

### Update config.yaml
```yaml
database:
  type: "mysql"  # Changed from "sqlite" or "postgresql"
  sqlite_path: "./job_automation.db"
  mysql:
    host: "localhost"
    port: 3306
    database: "job_automation"
    username: "job_user"
    password: "your_password"
    charset: "utf8mb4"
```

### Environment Variables
```bash
# .env file
DATABASE_URL=mysql://username:password@localhost:3306/job_automation
```

## 🔄 Migration from Existing Database

### From SQLite
```bash
# 1. Backup existing data
cp job_automation.db job_automation_backup.db

# 2. Run migration script
python migrate_to_mysql.py

# 3. Verify migration
python test_system.py
```

### From PostgreSQL
```bash
# 1. Export data (if needed)
pg_dump -h localhost -U username -d job_automation > backup.sql

# 2. Update config.yaml manually
# 3. Test connection
python test_system.py
```

## 🧪 Testing

### Test MySQL Connection
```bash
python test_system.py
```

### Test Database Operations
```bash
python cli.py init
python cli.py status
```

## 🐛 Troubleshooting

### Common Issues

#### 1. MySQL Connection Error
```bash
# Check MySQL service
sudo systemctl status mysql

# Check MySQL is running
sudo systemctl start mysql

# Verify connection
mysql -u username -p -h localhost
```

#### 2. Authentication Error
```bash
# Reset MySQL root password
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'new_password';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. Character Set Issues
```bash
# Check current charset
mysql -u username -p -e "SHOW VARIABLES LIKE 'character_set%';"

# Set charset in MySQL config
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

#### 4. Python MySQL Client Issues
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-dev default-libmysqlclient-dev build-essential

# Reinstall Python package
pip uninstall mysqlclient
pip install mysqlclient
```

### Debug Mode
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python test_system.py
```

## 📊 Performance Considerations

### MySQL Optimizations
```sql
-- Create indexes for better performance
CREATE INDEX idx_jobs_company ON jobs_clean(company);
CREATE INDEX idx_jobs_location ON jobs_clean(location);
CREATE INDEX idx_jobs_skills ON jobs_clean(skills);
CREATE INDEX idx_posts_status ON posts_ready(status);
CREATE INDEX idx_posts_platform ON posts_ready(platform);
```

### Connection Pooling
The application automatically handles connection pooling through SQLAlchemy.

## 🔒 Security Best Practices

### 1. User Permissions
```sql
-- Create dedicated user with minimal privileges
CREATE USER 'job_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON job_automation.* TO 'job_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Network Security
```sql
-- Restrict connections to localhost only
CREATE USER 'job_user'@'127.0.0.1' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON job_automation.* TO 'job_user'@'127.0.0.1';
```

### 3. Password Policy
```sql
-- Set password validation
SET GLOBAL validate_password.policy=MEDIUM;
SET GLOBAL validate_password.length=8;
```

## 📈 Monitoring

### MySQL Status
```sql
-- Check server status
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Slow_queries';
```

### Application Logs
```bash
# Monitor application logs
tail -f logs/job_automation.log

# Check for database errors
grep -i "database\|mysql\|connection" logs/job_automation.log
```

## 🔄 Rollback

### Back to SQLite
```yaml
# config.yaml
database:
  type: "sqlite"
  sqlite_path: "./job_automation.db"
```

### Back to PostgreSQL
```yaml
# config.yaml
database:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "job_automation"
    username: "username"
    password: "password"
```

## 📚 Additional Resources

- [MySQL Documentation](https://dev.mysql.com/doc/)
- [SQLAlchemy MySQL Dialect](https://docs.sqlalchemy.org/en/14/dialects/mysql.html)
- [MySQL Performance Tuning](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs: `tail -f logs/job_automation.log`
3. Check MySQL logs: `sudo tail -f /var/log/mysql/error.log`
4. Run system tests: `python test_system.py`
5. Verify MySQL connection: `mysql -u username -p -h localhost`

## ✅ Migration Checklist

- [ ] MySQL server installed and running
- [ ] Python MySQL client installed (`mysqlclient`)
- [ ] Database and user created
- [ ] Configuration updated (`config.yaml`)
- [ ] Connection tested (`python test_system.py`)
- [ ] Database initialized (`python cli.py init`)
- [ ] Application tested with MySQL
- [ ] Old database backed up (if applicable)
- [ ] Performance monitoring configured
- [ ] Security settings reviewed

