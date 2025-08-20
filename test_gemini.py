"""
Test script to verify Gemini API integration.
"""
import os
import sys
from loguru import logger

def test_gemini_import():
    """Test Gemini API import."""
    try:
        import google.generativeai as genai
        logger.success("✓ google-generativeai imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import google-generativeai: {e}")
        return False

def test_gemini_configuration():
    """Test Gemini API configuration."""
    try:
        import google.generativeai as genai
        
        # Check if API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("⚠ GOOGLE_API_KEY not set in environment")
            return False
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        logger.success("✓ Gemini API configured successfully")
        
        # Test model initialization
        model = genai.GenerativeModel('gemini-pro')
        logger.success("✓ Gemini Pro model initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Gemini configuration failed: {e}")
        return False

def test_gemini_text_generation():
    """Test basic text generation with Gemini."""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("⚠ GOOGLE_API_KEY not set, skipping text generation test")
            return True
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Simple test prompt
        prompt = "Generate a short, professional job posting caption for a Python developer position."
        
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            logger.success("✓ Gemini text generation successful")
            logger.info(f"Generated text: {response.text[:100]}...")
            return True
        else:
            logger.error("✗ Gemini text generation failed - no response")
            return False
            
    except Exception as e:
        logger.error(f"✗ Gemini text generation test failed: {e}")
        return False

def test_image_generation_module():
    """Test the image generation module."""
    try:
        from image_generator import ImageGenerationManager
        
        # Test initialization
        image_manager = ImageGenerationManager()
        logger.success("✓ Image generation manager initialized")
        
        # Test if output directory is created
        if os.path.exists("generated_images"):
            logger.success("✓ Generated images directory exists")
        else:
            logger.warning("⚠ Generated images directory not created yet")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Image generation module test failed: {e}")
        return False

def main():
    """Run all Gemini tests."""
    logger.info("Starting Gemini API integration tests...")
    logger.info("=" * 50)
    
    tests = [
        ("Gemini Import", test_gemini_import),
        ("Gemini Configuration", test_gemini_configuration),
        ("Gemini Text Generation", test_gemini_text_generation),
        ("Image Generation Module", test_image_generation_module),
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
        logger.success("🎉 All Gemini tests passed! Integration is working correctly.")
        return True
    else:
        logger.error(f"❌ {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    # Setup basic logging
    logger.add(sys.stderr, level="INFO")
    
    success = main()
    sys.exit(0 if success else 1)

