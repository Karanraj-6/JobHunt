"""
Image generation using Gemini API for job postings.
Generates professional images of company logos with job information.
"""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential


class GeminiImageGenerator:
    """Generates images using Gemini API for job postings."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Gemini image generator."""
        self.config_path = config_path
        self.config = self._load_config()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.config["image_generation"]["model"])
        
        # Create output directory
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Gemini Image Generator initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_job_image(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate an image for a job posting using Gemini.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Path to the generated image file, or None if generation failed
        """
        try:
            # Extract job information
            company_name = job_data.get("company_name", "Company")
            job_title = job_data.get("title", "Job Position")
            location = job_data.get("location", "Location")
            skills = job_data.get("skills", [])
            
            # Create prompt for image generation
            prompt = self._build_image_prompt(company_name, job_title, location, skills)
            
            logger.info(f"Generating image for {company_name} - {job_title}")
            
            # Generate image using Gemini
            response = self.model.generate_content(prompt)
            
            if response and hasattr(response, 'parts'):
                # Extract image data from response
                image_data = self._extract_image_from_response(response)
                if image_data:
                    # Save the generated image
                    filename = f"{company_name}_{job_title}_{job_data.get('id', 'job')}.png"
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filepath = self.output_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    logger.info(f"Image generated successfully: {filepath}")
                    return str(filepath)
            
            # Fallback to template-based image generation
            logger.warning("Gemini image generation failed, using template fallback")
            return self._generate_template_image(job_data)
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            # Fallback to template-based generation
            return self._generate_template_image(job_data)
    
    def _build_image_prompt(self, company_name: str, job_title: str, 
                           location: str, skills: list) -> str:
        """Build a detailed prompt for Gemini image generation."""
        skills_text = ", ".join(skills[:5]) if skills else "technology"
        
        prompt = f"""
        Create a professional, modern image for a job posting with the following specifications:
        
        Company: {company_name}
        Job Title: {job_title}
        Location: {location}
        Skills: {skills_text}
        
        Style Requirements:
        - Professional and corporate aesthetic
        - Clean, minimalist design
        - Company logo prominently displayed (if recognizable)
        - Job title clearly visible
        - Modern typography and layout
        - Professional color scheme (blues, grays, whites)
        - Subtle background patterns or gradients
        - Include visual elements representing the job role
        - High contrast for readability
        - Suitable for social media platforms (LinkedIn, X)
        
        The image should look like a professional job posting card that would attract top talent.
        """
        
        return prompt.strip()
    
    def _extract_image_from_response(self, response) -> Optional[bytes]:
        """Extract image data from Gemini response."""
        try:
            # This is a placeholder - actual implementation depends on Gemini's response format
            # You may need to adjust this based on the actual Gemini API response structure
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                        return part.inline_data.data
            return None
        except Exception as e:
            logger.error(f"Failed to extract image from response: {e}")
            return None
    
    def _generate_template_image(self, job_data: Dict[str, Any]) -> str:
        """
        Generate a template-based image as fallback when Gemini fails.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Path to the generated template image
        """
        try:
            # Create a simple template image
            width, height = 1024, 1024
            image = Image.new('RGB', (width, height), color='#f8f9fa')
            draw = ImageDraw.Draw(image)
            
            # Try to load a default font, fallback to default if not available
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_medium = ImageFont.truetype("arial.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw company name
            company_name = job_data.get("company_name", "Company")
            draw.text((width//2, 200), company_name, fill='#2c3e50', font=font_large, anchor="mm")
            
            # Draw job title
            job_title = job_data.get("title", "Job Position")
            draw.text((width//2, 300), job_title, fill='#34495e', font=font_medium, anchor="mm")
            
            # Draw location
            location = job_data.get("location", "Location")
            draw.text((width//2, 400), location, fill='#7f8c8d', font=font_small, anchor="mm")
            
            # Draw skills
            skills = job_data.get("skills", [])
            if skills:
                skills_text = "Skills: " + ", ".join(skills[:3])
                draw.text((width//2, 500), skills_text, fill='#95a5a6', font=font_small, anchor="mm")
            
            # Add a simple border
            draw.rectangle([50, 50, width-50, height-50], outline='#3498db', width=3)
            
            # Save the template image
            filename = f"template_{job_data.get('company_name', 'company')}_{job_data.get('id', 'job')}.png"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filepath = self.output_dir / filename
            
            image.save(filepath, 'PNG')
            logger.info(f"Template image generated: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate template image: {e}")
            return None
    
    def cleanup_old_images(self, max_age_hours: int = 24):
        """Clean up old generated images to save disk space."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for image_file in self.output_dir.glob("*.png"):
                if current_time - image_file.stat().st_mtime > max_age_seconds:
                    image_file.unlink()
                    logger.info(f"Cleaned up old image: {image_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {e}")


class ImageGenerationManager:
    """Manages image generation for multiple jobs."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the image generation manager."""
        self.config_path = config_path
        self.config = self._load_config()
        self.generator = GeminiImageGenerator(config_path)
        
        # Check if image generation is enabled
        if not self.config.get("image_generation", {}).get("enabled", False):
            logger.warning("Image generation is disabled in configuration")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def generate_images_for_jobs(self, jobs: list) -> Dict[str, str]:
        """
        Generate images for a list of jobs.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary mapping job IDs to image file paths
        """
        if not self.config.get("image_generation", {}).get("enabled", False):
            logger.info("Image generation is disabled, skipping image generation")
            return {}
        
        job_images = {}
        
        for job in jobs:
            try:
                job_id = str(job.get("id", "unknown"))
                image_path = self.generator.generate_job_image(job)
                
                if image_path:
                    job_images[job_id] = image_path
                    logger.info(f"Generated image for job {job_id}: {image_path}")
                else:
                    logger.warning(f"Failed to generate image for job {job_id}")
                    
            except Exception as e:
                logger.error(f"Error generating image for job {job.get('id', 'unknown')}: {e}")
                continue
        
        # Cleanup old images
        self.generator.cleanup_old_images()
        
        return job_images
    
    def get_image_for_job(self, job_id: str) -> Optional[str]:
        """Get the image path for a specific job."""
        # This would typically check if an image exists for the job
        # For now, we'll return None as images are generated on-demand
        return None

