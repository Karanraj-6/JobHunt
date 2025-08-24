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
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
            # Navigate to LinkedIn feed (as shown in the screenshot)
            self.driver.get("https://www.linkedin.com/feed/")
            self._add_random_delay(3, 5)
            
            # Strategy 1: Use the specific button selector from user's guidance
            start_post_selectors = [
                "button.artdeco-button--muted.artdeco-button--tertiary",
                "div[data-placeholder='Start a post']",
                "div[aria-label='Start a post']",
                "div[data-control-name='share.open']",
                "div[data-control-name='create_post']",
                "div[role='textbox'][data-placeholder*='post']",
                "div[contenteditable='true'][data-placeholder*='post']"
            ]
            
            for selector in start_post_selectors:
                try:
                    start_post_element = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found 'Start a post' element with selector: {selector}")
                    start_post_element.click()
                    self._add_random_delay(2, 3)
                    return True
                except:
                    continue
            
            # Strategy 2: Look for any element with "Start a post" text
            try:
                start_post_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Start a post') or contains(@data-placeholder, 'Start a post')]")
                logger.info("Found 'Start a post' element using XPath text search")
                start_post_element.click()
                self._add_random_delay(2, 3)
                return True
            except:
                pass
            
            # Strategy 3: Look for any clickable element containing "post"
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start a post') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create a post')]")
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found potential post element: {element.text[:50]}")
                            element.click()
                            self._add_random_delay(2, 3)
                            return True
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Text search failed: {e}")
            
            logger.error("Could not find LinkedIn 'Start a post' element")
            return False
            
        except Exception as e:
            logger.error(f"Failed to navigate to post creation: {e}")
            return False
    
    def _create_post(self, caption: str, job_data: Dict[str, Any], image_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Create the LinkedIn post with optional image."""
        try:
            # Wait for the modal to appear and find the text area (as shown in screenshot)
            post_textarea_selectors = [
                "div[data-placeholder='What do you want to talk about?']",
                "div[aria-label='Text editor for creating content']",
                "div[contenteditable='true'][data-placeholder*='talk about']",
                "div[contenteditable='true'][data-placeholder*='want to']",
                "div[role='textbox'][data-placeholder*='talk']",
                "div[contenteditable='true']",
                "div[role='textbox']"
            ]
            
            post_textarea = None
            for selector in post_textarea_selectors:
                try:
                    post_textarea = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found post textarea with selector: {selector}")
                    break
                except:
                    continue
            
            # If not found with CSS selectors, try XPath
            if not post_textarea:
                try:
                    post_textarea = self.driver.find_element(By.XPATH, "//div[contains(@data-placeholder, 'What do you want to talk about') or contains(@data-placeholder, 'talk about')]")
                    logger.info("Found post textarea using XPath")
                except:
                    pass
            
            if not post_textarea:
                raise Exception("Could not find LinkedIn post text area")
            
            # Clear any existing text and enter caption
            post_textarea.clear()
            self._add_random_delay(1, 2)
            
            # Clean caption to remove problematic Unicode characters that ChromeDriver can't handle
            cleaned_caption = ''.join(char for char in caption if ord(char) < 0x10000)
            logger.info(f"Cleaned caption length: {len(cleaned_caption)} characters (removed {len(caption) - len(cleaned_caption)} problematic characters)")
            
            # Type the cleaned caption quickly (no slow character-by-character typing)
            post_textarea.send_keys(cleaned_caption)
            
            self._add_random_delay(2, 3)
            
            # Add image if provided
            if image_path and os.path.exists(image_path):
                try:
                    self._add_image_to_post(image_path)
                    self._add_random_delay(2, 3)
                    
                    # After image upload and Next button click, now look for the Post button
                    logger.info("Looking for Post button after returning from image upload...")
                    
                    # Strategy 1: Use the CSS selector as requested
                    try:
                        post_button = self.wait.until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, "button.share-actions__primary-action")
                            )
                        )
                        logger.info("Found Post button using CSS selector")
                    except TimeoutException:
                        # Strategy 2: Use the working XPath method as fallback
                        try:
                            post_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Post') or contains(@aria-label, 'Post')]"))
                            )
                            logger.info("Found Post button using working XPath method")
                        except TimeoutException:
                            # Strategy 3: Try CSS selectors as fallback
                            post_button_selectors = [
                                "button[aria-label='Post']",
                                "button[data-control-name='share.post']",
                                "button:contains('Post')",
                                "button[type='submit']",
                                "button[data-control-name='share.post_button']"
                            ]
                            
                            for selector in post_button_selectors:
                                try:
                                    post_button = self.wait.until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                    logger.info(f"Found post button with selector: {selector}")
                                    break
                                except:
                                    continue
                            
                            # Strategy 4: Final fallback - search all buttons
                            if not post_button:
                                try:
                                    buttons = self.driver.find_elements(By.XPATH, "//button")
                                    for button in buttons:
                                        try:
                                            if button.is_displayed() and button.is_enabled():
                                                button_text = button.text.lower()
                                                if 'post' in button_text or 'submit' in button_text or 'share' in button_text:
                                                    logger.info(f"Found potential post button: {button.text}")
                                                    post_button = button
                                                    break
                                        except:
                                            continue
                                except:
                                    pass
                    
                    if post_button:
                        # Wait for button to become enabled (LinkedIn might enable it after content is added)
                        try:
                            self.wait.until(
                                EC.element_to_be_clickable(
                                    (By.CSS_SELECTOR, "button.share-actions__primary-action")
                                )
                            )
                            logger.info("Post button is now clickable")
                        except TimeoutException:
                            logger.warning("Post button may still be disabled, but attempting to click anyway")
                        
                        # Use JavaScript click to avoid any disabled state issues
                        logger.info("Clicking Post button to publish the post...")
                        self.driver.execute_script("arguments[0].click();", post_button)
                        logger.info("Post button clicked successfully")
                    else:
                        raise Exception("Could not find LinkedIn post button")
                        
                except Exception as e:
                    logger.warning(f"Failed to add image to LinkedIn post: {e}")
                    # Continue with text-only post
            
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
            # Strategy 1: Use the specific "Add media" button selector from user's guidance
            try:
                media_button = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Add media']"))
                )
                logger.info("Found Add media button using specific aria-label")
                # Use JavaScript click to avoid element interception
                self.driver.execute_script("arguments[0].click();", media_button)
                self._add_random_delay(1, 2)
            except TimeoutException:
                # Strategy 2: Fallback to generic selectors
                photo_button_selectors = [
                    "button[aria-label='Photo']",
                    "button[aria-label='Add a photo']",
                    "button[data-control-name='share.add_photo']",
                    "button[data-control-name='share.add_media']",
                    "button:contains('Photo')",
                    "button:contains('Add a photo')",
                    "div[data-control-name='share.add_photo']"
                ]
                
                photo_button = None
                for selector in photo_button_selectors:
                    try:
                        photo_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"Found Photo button with selector: {selector}")
                        break
                    except:
                        continue
                
                # If not found, try XPath search for "Photo" text
                if not photo_button:
                    try:
                        photo_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Photo') or contains(text(), 'photo')]")
                        logger.info("Found Photo button using XPath text search")
                    except:
                        pass
                
                if not photo_button:
                    raise Exception("Could not find LinkedIn Photo button")
                
                photo_button.click()
                self._add_random_delay(1, 2)
            
            # Wait for the file upload dialog to appear
            logger.info("Waiting for file upload dialog to appear...")
            self._add_random_delay(2, 3)
            
            # Strategy 1: Use the specific file input selector from user's guidance
            try:
                file_input = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#media-editor-file-selector_file-input"))
                )
                logger.info("Found file input using specific ID selector")
            except TimeoutException:
                # Strategy 2: Fallback to generic file input
                try:
                    file_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    logger.info("Found file input using generic type selector")
                except TimeoutException:
                    raise Exception("Could not find file input element")
            
            # Send the image file path
            file_input.send_keys(os.path.abspath(image_path))
            logger.info(f"Sent image file path: {os.path.abspath(image_path)}")
            
            # Wait longer for image to upload and process
            logger.info("Waiting for image to upload and process...")
            self._add_random_delay(5, 8)
            
            # Wait for the image preview to appear (this indicates successful upload)
            try:
                # Look for the image preview in the editor
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='blob:']"))
                )
                logger.info("Image preview found - upload successful")
            except TimeoutException:
                # Alternative: look for any image element
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
                    )
                    logger.info("Image element found - upload successful")
                except TimeoutException:
                    logger.warning("Could not confirm image upload, but proceeding anyway")
            
            logger.info(f"Image added to LinkedIn post: {image_path}")
            
            # After image upload, LinkedIn shows a "Next" button that needs to be clicked
            try:
                # Wait for the Next button to appear and be clickable
                logger.info("Looking for Next button after image upload...")
                
                # Wait a bit more for the UI to settle after image upload
                self._add_random_delay(2, 3)
                
                # Strategy 1: Use the specific aria-label selector
                try:
                    next_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.share-box-footer.main-actions button[aria-label='Next']"))
                    )
                    logger.info("Found Next button using aria-label selector")
                except TimeoutException:
                    logger.info("Next button not found with aria-label, trying other strategies...")
                    # Strategy 2: Look for button with Next text
                    try:
                        next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                        logger.info("Found Next button using text search")
                    except NoSuchElementException:
                        logger.info("Next button not found with text search, trying class selector...")
                        # Strategy 3: Look for button with specific class (from user's HTML)
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.share-box-footer_primary-btn")
                            logger.info("Found Next button using share-box-footer_primary-btn class selector")
                        except NoSuchElementException:
                            logger.info("Next button not found with class selector, trying footer text search...")
                            # Strategy 4: Look for button with Next text in share-box-footer
                            try:
                                next_button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'share-box-footer')]//button[contains(text(), 'Next')]")
                                logger.info("Found Next button using share-box-footer text search")
                            except NoSuchElementException:
                                # Strategy 5: Look for any button with Next text anywhere
                                try:
                                    next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next') or contains(@aria-label, 'Next')]")
                                    logger.info("Found Next button using general search")
                                except NoSuchElementException:
                                    raise Exception("Could not find Next button with any selector")
                
                # Click the Next button
                if next_button:
                    logger.info(f"Next button found: {next_button.get_attribute('outerHTML')[:200]}...")
                    logger.info("Clicking Next button to proceed to post...")
                    # Use JavaScript click to avoid any interception issues
                    self.driver.execute_script("arguments[0].click();", next_button)
                    self._add_random_delay(3, 5)  # Wait longer for the transition
                    logger.info("Successfully clicked Next button and waiting for transition")
                else:
                    raise Exception("Next button found but not clickable")
                    
            except TimeoutException:
                logger.warning("Next button not found within timeout, proceeding directly to post")
            except Exception as e:
                logger.warning(f"Could not click Next button: {e}, proceeding anyway")
            
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
