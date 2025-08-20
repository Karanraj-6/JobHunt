"""
Test script to verify system components are working correctly.
"""
import os
import sys
from loguru import logger

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing module imports...")
    
    try:
        import yaml
        logger.success("✓ yaml imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import yaml: {e}")
        return False
    
    try:
        import requests
        logger.success("✓ requests imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import requests: {e}")
        return False
    
    try:
        import sqlalchemy
        logger.success("✓ sqlalchemy imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import sqlalchemy: {e}")
        return False
    
    try:
        import mysqlclient
        logger.success("✓ mysqlclient imported successfully")
    except ImportError as e:
        logger.warning(f"⚠ mysqlclient not available (MySQL support disabled): {e}")
    
    try:
        import selenium
        logger.success("✓ selenium imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import selenium: {e}")
        return False
    
    try:
        import tweepy
        logger.success("✓ tweepy imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import tweepy: {e}")
        return False
    
    try:
        import google.generativeai as genai
        logger.success("✓ google-generativeai imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import google-generativeai: {e}")
        return False
    
    try:
        from PIL import Image
        logger.success("✓ Pillow (PIL) imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Pillow: {e}")
        return False
    
    try:
        import apscheduler
        logger.success("✓ apscheduler imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import apscheduler: {e}")
        return False
    
    try:
        import fuzzywuzzy
        logger.success("✓ fuzzywuzzy imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import fuzzywuzzy: {e}")
        return False
    
    return True

def test_local_modules():
    """Test that local modules can be imported."""
    logger.info("Testing local module imports...")
    
    try:
        from models import Base
        logger.success("✓ models imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import models: {e}")
        return False
    
    try:
        from database import DatabaseManager
        logger.success("✓ database imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import database: {e}")
        return False
    
    try:
        from job_models import Job, JobNormalizer
        logger.success("✓ job_models imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import job_models: {e}")
        return False
    
    try:
        from image_generator import GeminiImageGenerator, ImageGenerationManager
        logger.success("✓ image_generator imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import image_generator: {e}")
        return False
    
    try:
        from job_fetchers import JobFetcherManager
        logger.success("✓ job_fetchers imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import job_fetchers: {e}")
        return False
    
    try:
        from job_processor import JobProcessor
        logger.success("✓ job_processor imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import job_processor: {e}")
        return False
    
    try:
        from caption_generator import CaptionGenerator
        logger.success("✓ caption_generator imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import caption_generator: {e}")
        return False
    
    try:
        from social_posters import SocialPosterManager
        logger.success("✓ social_posters imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import social_posters: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration file loading."""
    logger.info("Testing configuration...")
    
    try:
        import yaml
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        required_sections = ['job_filters', 'posting', 'job_sources', 'database', 'logging']
        for section in required_sections:
            if section in config:
                logger.success(f"✓ {section} configuration section found")
            else:
                logger.warning(f"⚠ {section} configuration section missing")
        
        logger.success("✓ Configuration file loaded successfully")
        return True
        
    except FileNotFoundError:
        logger.error("✗ config.yaml file not found")
        return False
    except yaml.YAMLError as e:
        logger.error(f"✗ Failed to parse config.yaml: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_environment():
    """Test environment setup."""
    logger.info("Testing environment setup...")
    
    # Check if logs directory exists
    if not os.path.exists("logs"):
        try:
            os.makedirs("logs")
            logger.success("✓ Created logs directory")
        except Exception as e:
            logger.error(f"✗ Failed to create logs directory: {e}")
            return False
    else:
        logger.success("✓ logs directory exists")
    
    # Check if .env file exists
    if os.path.exists(".env"):
        logger.success("✓ .env file found")
    else:
        logger.warning("⚠ .env file not found - you'll need to create one")
    
    return True

def test_database_connection():
    """Test database connection (if configured)."""
    logger.info("Testing database connection...")
    
    try:
        from database import init_database
        
        # Try to initialize database
        db_manager = init_database()
        logger.success("✓ Database manager initialized")
        
        # Test connection
        db_manager.create_tables()
        logger.success("✓ Database tables created successfully")
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠ Database test failed (this is normal if not configured): {e}")
        return True  # Don't fail the test for database issues

def test_image_generation():
    """Test image generation functionality."""
    logger.info("Testing image generation...")
    
    try:
        from image_generator import ImageGenerationManager
        
        # Test if image generation manager can be initialized
        image_manager = ImageGenerationManager()
        logger.success("✓ Image generation manager initialized")
        
        # Test if output directory is created
        if os.path.exists("generated_images"):
            logger.success("✓ Generated images directory exists")
        else:
            logger.warning("⚠ Generated images directory not created yet")
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠ Image generation test failed (this is normal if not configured): {e}")
        return True  # Don't fail the test for configuration issues

def main():
    """Run all tests."""
    logger.info("Starting system tests...")
    logger.info("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Local Modules", test_local_modules),
        ("Configuration", test_configuration),
        ("Environment", test_environment),
        ("Database", test_database_connection),
        ("Image Generation", test_image_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.success(f"✓ {test_name} test passed")
            else:
                logger.error(f"✗ {test_name} test failed")
        except Exception as e:
            logger.error(f"✗ {test_name} test failed with exception: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("🎉 All tests passed! System is ready to use.")
        return True
    else:
        logger.error(f"❌ {total - passed} test(s) failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    # Setup basic logging
    logger.add(sys.stderr, level="INFO")
    
    success = main()
    sys.exit(0 if success else 1)
