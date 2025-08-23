"""
Social media posting automation for LinkedIn.
"""
import os
import time
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_exponential
import yaml

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

class BaseSocialPoster:
    """Base class for social media posters."""
    
    def __init__(self, config: dict):
        """Initialize the poster."""
        self.config = config
        self.posting_config = config.get('posting', {})
    
    def post_content(self, caption: str, job_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Post content to the platform. Override in subclasses."""
        raise NotImplementedError
    
    def _add_random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay to avoid detection."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

class LinkedInPoster(BaseSocialPoster):
    """LinkedIn poster using Selenium automation."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables are required")
        
        self.driver = None
        self.wait = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome driver with appropriate options."""
        try:
            chrome_options = Options()
            
            # Add options to avoid detection
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use webdriver manager to handle driver installation
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("LinkedIn Chrome driver setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup LinkedIn driver: {e}")
            raise
    
    def _login(self) -> bool:
        """Login to LinkedIn."""
        try:
            logger.info("Attempting to login to LinkedIn")
            
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            self._add_random_delay(2, 4)
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            self._add_random_delay(1, 2)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            self._add_random_delay(1, 2)
            
            # Click sign in button
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            # Wait for login to complete
            self._add_random_delay(3, 5)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.success("LinkedIn login successful")
                return True
            else:
                logger.error("LinkedIn login failed - unexpected redirect")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            return False
    
    def _navigate_to_post_creation(self) -> bool:
        """Navigate to LinkedIn post creation area."""
        try:
            # Navigate to LinkedIn home
            self.driver.get("https://www.linkedin.com/feed/")
            self._add_random_delay(2, 4)
            
            # Find and click the "Start a post" button
            start_post_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Start a post']"))
            )
            start_post_button.click()
            self._add_random_delay(1, 2)
            
            logger.info("Navigated to LinkedIn post creation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to post creation: {e}")
            return False
    
    def _create_post(self, caption: str, job_data: Dict[str, Any], image_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Create the LinkedIn post with optional image."""
        try:
            # Wait for post text area to appear
            post_textarea = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Text editor for creating content']"))
            )
            
            # Clear any existing text and enter caption
            post_textarea.clear()
            self._add_random_delay(1, 2)
            
            # Type the caption with human-like delays
            for char in caption:
                post_textarea.send_keys(char)
                if random.random() < 0.1:  # 10% chance of small delay
                    time.sleep(random.uniform(0.05, 0.15))
            
            self._add_random_delay(2, 3)
            
            # Add image if provided
            if image_path and os.path.exists(image_path):
                try:
                    self._add_image_to_post(image_path)
                    self._add_random_delay(2, 3)
                except Exception as e:
                    logger.warning(f"Failed to add image to LinkedIn post: {e}")
                    # Continue with text-only post
            
            # Click Post button
            post_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Post']"))
            )
            post_button.click()
            
            # Wait for post to complete
            self._add_random_delay(3, 5)
            
            # Try to get the post URL (this might not be immediately available)
            try:
                # Look for success message or redirect
                if "feed" in self.driver.current_url:
                    logger.success("LinkedIn post created successfully")
                    # Note: Getting the exact post URL immediately after posting is challenging
                    # We'll return a placeholder that can be updated later
                    return True, "linkedin_post_created"
                else:
                    logger.warning("LinkedIn post status unclear")
                    return False, None
                    
            except Exception as e:
                logger.warning(f"Could not verify post URL: {e}")
                return True, "linkedin_post_created"
                
        except Exception as e:
            logger.error(f"Failed to create LinkedIn post: {e}")
            return False, None
    
    def _add_image_to_post(self, image_path: str):
        """Add an image to the LinkedIn post."""
        try:
            # Look for the image upload button
            image_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Add media']"))
            )
            image_button.click()
            self._add_random_delay(1, 2)
            
            # Find the file input element
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            
            # Send the image file path
            file_input.send_keys(os.path.abspath(image_path))
            self._add_random_delay(2, 4)
            
            # Wait for image to upload and process
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt*='uploaded']"))
            )
            
            logger.info(f"Image added to LinkedIn post: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to add image to LinkedIn post: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def post_content(self, caption: str, job_data: Dict[str, Any], image_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Post content to LinkedIn with optional image."""
        try:
            # Ensure we're logged in
            if not self._is_logged_in():
                if not self._login():
                    return False, "login_failed"
            
            # Navigate to post creation
            if not self._navigate_to_post_creation():
                return False, "navigation_failed"
            
            # Create the post
            success, post_id = self._create_post(caption, job_data, image_path)
            
            if success:
                logger.info(f"LinkedIn post created for job: {job_data.get('title', 'Unknown')}")
            else:
                logger.error(f"LinkedIn post failed for job: {job_data.get('title', 'Unknown')}")
            
            return success, post_id
            
        except Exception as e:
            logger.error(f"LinkedIn posting error: {e}")
            return False, str(e)
    
    def _is_logged_in(self) -> bool:
        """Check if currently logged into LinkedIn."""
        try:
            # Check for elements that indicate we're logged in
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Start a post']")
            return True
        except NoSuchElementException:
            return False
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            logger.info("LinkedIn driver closed")
class SocialPosterManager:
    """Manages all social media posters."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the poster manager."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.posters = {}
        self._posters_initialized = False  # Don't initialize immediately
    
    def _initialize_posters(self):
        """Initialize all enabled social media posters."""
        if self._posters_initialized:
            return
            
        platforms = self.config.get('posting', {}).get('platforms', [])
        
        if 'linkedin' in platforms:
            try:
                self.posters['linkedin'] = LinkedInPoster(self.config)
                logger.info("LinkedIn poster initialized")
            except Exception as e:
                logger.error(f"Failed to initialize LinkedIn poster: {e}")
        
        self._posters_initialized = True
        logger.info(f"Initialized {len(self.posters)} social media posters")
    
    def _ensure_posters_initialized(self):
        """Ensure posters are initialized before use."""
        if not self._posters_initialized:
            self._initialize_posters()
    
    def post_to_all_platforms(self, captions: Dict[str, str], job_data: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Post to all enabled platforms with optional image."""
        # Initialize posters only when actually needed for posting
        self._ensure_posters_initialized()
        
        results = {}
        
        for platform, poster in self.posters.items():
            if platform in captions:
                try:
                    caption = captions[platform]
                    success, post_id = poster.post_content(caption, job_data, image_path)
                    results[platform] = (success, post_id)
                    
                    if success:
                        logger.info(f"Successfully posted to {platform}")
                    else:
                        logger.error(f"Failed to post to {platform}: {post_id}")
                        
                except Exception as e:
                    logger.error(f"Error posting to {platform}: {e}")
                    results[platform] = (False, str(e))
            else:
                logger.warning(f"No caption available for {platform}")
                results[platform] = (False, "no_caption")
        
        return results
    
    def close_all_posters(self):
        """Close all poster resources."""
        for platform, poster in self.posters.items():
            try:
                if hasattr(poster, 'close'):
                    poster.close()
                logger.info(f"Closed {platform} poster")
            except Exception as e:
                logger.error(f"Error closing {platform} poster: {e}")
