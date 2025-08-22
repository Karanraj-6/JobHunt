#!/usr/bin/env python3
"""
System-wide test script for the Job Automation System.
Tests all major components and dependencies.
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Environment variables loaded from .env file")
except ImportError:
    print("⚠ python-dotenv not installed, environment variables may not be loaded")

def test_imports():
    """Test all required package imports."""
    print("Testing package imports...")
    
    try:
        import requests
        print("✓ requests")
    except ImportError:
        print("✗ requests - Install with: pip install requests")
        return False
    
    try:
        import yaml
        print("✓ PyYAML")
    except ImportError:
        print("✗ PyYAML - Install with: pip install PyYAML")
        return False
    
    try:
        import loguru
        print("✓ loguru")
    except ImportError:
        print("✗ loguru - Install with: pip install loguru")
        return False
    
    try:
        import tenacity
        print("✓ tenacity")
    except ImportError:
        print("✗ tenacity - Install with: pip install tenacity")
        return False
    
    try:
        import pymongo
        print("✓ pymongo")
    except ImportError:
        print("✗ pymongo - Install with: pip install pymongo")
        return False
    
    try:
        import google.generativeai
        print("✓ google-generativeai")
    except ImportError:
        print("✗ google-generativeai - Install with: pip install google-generativeai")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow")
    except ImportError:
        print("✗ Pillow - Install with: pip install Pillow")
        return False
    
    try:
        import selenium
        print("✓ selenium")
    except ImportError:
        print("✗ selenium - Install with: pip install selenium")
        return False
    
    try:
        import apscheduler
        print("✓ APScheduler")
    except ImportError:
        print("✗ APScheduler - Install with: pip install APScheduler")
        return False
    
    return True

def test_config_files():
    """Test configuration files exist."""
    print("\nTesting configuration files...")
    
    if os.path.exists('.env'):
        print("✓ .env file exists")
    else:
        print("✗ .env file missing - Create from env.template")
        return False
    
    if os.path.exists('config.yaml'):
        print("✓ config.yaml exists")
    else:
        print("✗ config.yaml missing")
        return False
    
    return True

def test_mongodb_connection():
    """Test MongoDB connectivity."""
    print("\nTesting MongoDB connection...")
    
    try:
        import pymongo
        from pymongo import MongoClient
        
        # Try to connect to MongoDB
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ MongoDB connection successful")
        
        # Test database access
        db = client['job_automation']
        collections = db.list_collection_names()
        print(f"✓ Database 'job_automation' accessible, collections: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("  Make sure MongoDB is running on localhost:27017")
        return False

def test_gemini_api():
    """Test Gemini API configuration."""
    print("\nTesting Gemini API configuration...")
    
    try:
        import google.generativeai as genai
        
        # Check if API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("✗ GOOGLE_API_KEY not set in environment")
            return False
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        
        # Test basic model access
        model = genai.GenerativeModel('gemini-pro')
        print("✓ Gemini API configured successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Gemini API test failed: {e}")
        return False

def test_image_generation():
    """Test image generation module."""
    print("\nTesting image generation module...")
    
    try:
        from image_generator import GeminiImageGenerator
        print("✓ Image generation module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Image generation module test failed: {e}")
        return False

def test_linkedin_credentials():
    """Test LinkedIn credentials."""
    print("\nTesting LinkedIn credentials...")
    
    linkedin_email = os.getenv('LINKEDIN_EMAIL')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')
    
    if linkedin_email and linkedin_password:
        print("✓ LinkedIn credentials found")
        return True
    else:
        print("✗ LinkedIn credentials missing - Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        return False

def test_job_sources():
    """Test job source configuration."""
    print("\nTesting job source configuration...")
    
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    jooble_key = os.getenv('JOOBLE_API_KEY')
    
    sources_found = []
    if rapidapi_key:
        sources_found.append("RapidAPI (Indeed)")
    if jooble_key:
        sources_found.append("Jooble")
    
    if sources_found:
        print(f"✓ Job sources configured: {', '.join(sources_found)}")
        return True
    else:
        print("✗ No job sources configured - Set RAPIDAPI_KEY and/or JOOBLE_API_KEY")
        return False

def main():
    """Run all tests."""
    print("Job Automation System - System Test")
    print("=" * 40)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration Files", test_config_files),
        ("MongoDB Connection", test_mongodb_connection),
        ("Gemini API", test_gemini_api),
        ("Image Generation", test_image_generation),
        ("LinkedIn Credentials", test_linkedin_credentials),
        ("Job Sources", test_job_sources),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. python cli.py init")
        print("2. python cli.py fetch")
        print("3. python cli.py post")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Start MongoDB service")
        print("- Set required environment variables in .env file")
        print("- Check config.yaml configuration")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
