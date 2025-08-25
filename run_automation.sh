#!/bin/bash

# Job Automation System - Production Deployment Script
# For Linux/Mac production deployment

echo "========================================"
echo "  JOB AUTOMATION SYSTEM - PRODUCTION"
echo "========================================"
echo ""
echo "Starting automation system..."
echo "This will run the complete automation:"
echo "- Fetch jobs from APIs"
echo "- Process and filter jobs"
echo "- Generate captions"
echo "- Post to LinkedIn"
echo "- Run continuously"
echo ""
echo "Press Ctrl+C to stop the system"
echo ""
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if required files exist
if [ ! -f "run_automation.py" ]; then
    echo "❌ Error: run_automation.py not found"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    echo "❌ Error: config.yaml not found"
    exit 1
fi

echo "✅ All required files found"
echo "🚀 Starting automation system..."

# Run the automation
python3 run_automation.py

echo ""
echo "========================================"
echo "Automation system stopped."
echo "Check logs/automation.log for details."
echo "========================================"

