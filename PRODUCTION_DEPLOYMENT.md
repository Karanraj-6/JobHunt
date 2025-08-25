# Production Deployment Guide

## 🚀 Main Production Entry Point

For **production deployment**, you have **ONE main file** to run:

### **Windows:**
```bash
run_automation.bat
```

### **Linux/Mac:**
```bash
./run_automation.sh
```

### **Direct Python:**
```bash
python run_automation.py
```

## 📋 What This Does

The production script (`run_automation.py`) runs the **complete automation system**:

✅ **Fetches jobs** from RapidAPI and Jooble  
✅ **Processes and filters** for entry-level positions (0-2 years)  
✅ **Generates captions** with your exact format  
✅ **Posts to LinkedIn** automatically  
✅ **Handles daily limits** (4 posts per day)  
✅ **Runs continuously** until stopped  
✅ **Logs everything** to `logs/automation.log`  

## 🔧 Production Setup

### **1. Prerequisites:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure these files exist:
- .env (with your API keys)
- config.yaml (configuration)
- run_automation.py (main script)
```

### **2. Environment Variables (.env):**
```bash
# MongoDB
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DB=Job_auto

# APIs
RAPIDAPI_KEY=your_rapidapi_key
JOOBLE_API_KEY=your_jooble_key

# LinkedIn
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Gemini (optional)
GEMINI_API_KEY=your_gemini_key
```

### **3. Configuration (config.yaml):**
- Database settings
- Job filtering rules
- Posting schedules
- Platform configurations

## 🚀 Deployment Commands

### **Windows Production:**
```bash
# Double-click or run:
run_automation.bat

# Or command line:
python run_automation.py
```

### **Linux/Mac Production:**
```bash
# Make executable first time:
chmod +x run_automation.sh

# Run:
./run_automation.sh

# Or direct Python:
python3 run_automation.py
```

### **Docker Production (Optional):**
```bash
# Build image
docker build -t job-automation .

# Run container
docker run -d --name job-automation job-automation
```

## 📊 Production Features

### **Logging:**
- **Console output** with colors
- **File logging** in `logs/automation.log`
- **Daily rotation** and compression
- **30-day retention**

### **Error Handling:**
- **Graceful shutdown** on Ctrl+C
- **Automatic retries** for API failures
- **Comprehensive error logging**
- **System health monitoring**

### **Monitoring:**
- **Real-time status** in console
- **Detailed logs** for debugging
- **Performance metrics**
- **Error tracking**

## 🔄 Production Workflow

### **Daily Operation:**
1. **Start system**: `run_automation.bat` (Windows) or `./run_automation.sh` (Linux/Mac)
2. **System runs automatically**:
   - Fetches fresh jobs every few hours
   - Filters for entry-level positions
   - Generates captions
   - Posts to LinkedIn (up to 4 posts/day)
3. **Monitor logs**: Check `logs/automation.log`
4. **Stop system**: Press Ctrl+C

### **Monthly Maintenance:**
```bash
# Monthly cleanup
python monthly_cleanup.py

# Then restart
run_automation.bat
```

## 🛠️ Production Management

### **Start Automation:**
```bash
# Windows
run_automation.bat

# Linux/Mac
./run_automation.sh
```

### **Stop Automation:**
```bash
# Press Ctrl+C in the terminal
# Or kill the process
```

### **Check Status:**
```bash
# View logs
tail -f logs/automation.log

# Check system status
python cli.py status

# View analytics
python cli.py analytics
```

### **Troubleshooting:**
```bash
# Test system
python test_system.py

# Check daily count
python check_daily_count.py

# Manual operations
python cli.py fetch
python cli.py generate-captions
python cli.py post
```

## 📁 Production File Structure

```
automation/
├── run_automation.py          # 🚀 MAIN PRODUCTION ENTRY POINT
├── run_automation.bat         # Windows deployment script
├── run_automation.sh          # Linux/Mac deployment script
├── .env                       # Environment variables
├── config.yaml               # Configuration
├── requirements.txt          # Python dependencies
├── logs/                     # Production logs
│   └── automation.log
├── orchestrator.py           # Core automation logic
├── job_fetchers.py          # API integrations
├── job_processor.py         # Job processing
├── caption_generator.py     # Caption generation
├── social_posters.py        # LinkedIn posting
└── database.py              # MongoDB connection
```

## 🎯 Summary

**For production deployment, you only need to run ONE file:**

### **Windows:**
```bash
run_automation.bat
```

### **Linux/Mac:**
```bash
./run_automation.sh
```

**This single command starts the complete automation system that runs everything automatically!** 🚀

