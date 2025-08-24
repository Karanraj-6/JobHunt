"""
Caption generation using Google Gemini AI.
"""
import os
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import google.generativeai as genai

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

import re
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential


class CaptionGenerator:
    """Generates social media captions using Gemini API."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the caption generator."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.posting_config = self.config.get('posting', {})
        self.caption_configs = self.posting_config.get('captions', {})
        self.llm_config = self.config.get('llm', {})
        
        # Initialize Gemini client
        self._init_gemini_client()
    
    def _init_gemini_client(self):
        """Initialize Gemini API client."""
        self.gemini_client = None
        
        # Initialize Gemini client
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key:
            try:
                genai.configure(api_key=google_api_key)
                model_name = self.llm_config.get('model', 'gemini-pro')
                self.gemini_client = genai.GenerativeModel(model_name)
                logger.info(f"Gemini client initialized successfully with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        else:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    def generate_captions(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate captions for all platforms."""
        captions = {}
        
        platforms = self.posting_config.get('platforms', ['linkedin'])
        
        for platform in platforms:
            try:
                caption = self._generate_platform_caption(jobs_data, platform)
                if caption:
                    captions[platform] = caption
                    logger.info(f"Generated {platform} caption for {len(jobs_data)} jobs.")
            except Exception as e:
                logger.error(f"Error generating {platform} caption: {e}")
                continue
        
        return captions
    
    def _generate_platform_caption(self, jobs_data: List[Dict[str, Any]], platform: str) -> Optional[str]:
        """Generate caption for a specific platform."""
        platform_config = self.caption_configs.get(platform, {})
        
        if platform == 'linkedin':
            return self._generate_linkedin_caption(jobs_data, platform_config)
        else:
            logger.warning(f"Unsupported platform: {platform}, defaulting to LinkedIn")
            return self._generate_linkedin_caption(jobs_data, platform_config)
    
    def _generate_linkedin_caption(self, jobs_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Optional[str]:
        """Generate LinkedIn caption."""
        prompt = self._build_linkedin_prompt(jobs_data, config)
        
        try:
            return self._generate_with_gemini(prompt, config)
        except Exception as e:
            logger.error(f"Error generating LinkedIn caption with Gemini: {e}")
            # For fallback, we'll just use the first job.
            return self._generate_fallback_caption(jobs_data[0], 'linkedin', config)
    
    def _build_linkedin_prompt(self, jobs_data: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build LinkedIn prompt for a list of jobs with a strict template."""
        hashtag_count = config.get('hashtag_count', 15)
        audience = config.get('audience', 'Indian tech professionals')
        
        jobs_str_list = []
        for i, job_data in enumerate(jobs_data):
            skills = ", ".join(job_data.get('skills', []))
            description = job_data.get('description', 'N/A')
            job_str = f"""
**Job {i+1}: {job_data.get('title', 'N/A')}**

- **Company:** {job_data.get('company', 'N/A')}
- **Role:** {job_data.get('title', 'N/A')}
- **Location:** {job_data.get('location', 'N/A')}
- **Experience Required:** {job_data.get('experience', 'N/A')}
- **Employment Type:** {job_data.get('employment_type', 'N/A')}
- **Salary/CTC:** {job_data.get('salary', 'Negotiable')}
- **Apply Link:** {job_data.get('apply_url', 'N/A')}

**Job Description:**
{description}

**Requirements:**
{skills}
"""
            jobs_str_list.append(job_str)
            
        jobs_section = "\n---\n".join(jobs_str_list) # Separator between jobs

        prompt = f"""You are a content creation assistant. Your only task is to assemble a single text post from the provided job details.

**CRITICAL FORMATTING REQUIREMENTS:**
1.  Each piece of information MUST be on a separate line
2.  Use EXACTLY this format with line breaks:
   
   Company Name: [Company Name]
   Role: [Job Title]
   Experience: [Experience requirements or N/A if not specified]
   Apply Link: [Insert link here]
   
3.  Use three dashes (---) as a separator between each job listing
4.  After all the job listings, add these EXACT hashtags:
   #HiringNow #JobAlert #CareerOpportunities #JobSearch #JobOpening #WeAreHiring
5.  Do not add any introductory text, titles, or summaries
6.  The output must start directly with the first job's details
7.  **MOST IMPORTANT: Use actual line breaks between Company Name, Role, Experience, and Apply Link**

**Example of required format:**
Company Name: Example Corp
Role: Developer
Experience: 2+ years
Apply Link: https://example.com

---

Company Name: Another Corp
Role: Senior Developer
Experience: 5+ years
Apply Link: https://another.com

#HiringNow #JobAlert #CareerOpportunities #JobSearch #JobOpening #WeAreHiring

**Job Listings to Combine:**
{jobs_section}
"""
        
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _generate_with_gemini(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate caption using Gemini."""
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.llm_config.get('max_tokens', 500),
                temperature=self.llm_config.get('temperature', 0.7),
                top_p=0.8,
                top_k=40
            )
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and hasattr(response, 'text'):
                caption = response.text.strip()
                return self._clean_caption(caption)
            else:
                raise ValueError("Invalid response from Gemini API")
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _clean_caption(self, caption: str) -> str:
        """Clean and format the generated caption."""
        # Remove extra whitespace
        caption = ' '.join(caption.split())
        
        # Ensure hashtags are properly formatted
        lines = caption.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Ensure hashtags start with #
                if line.startswith('hashtag') or line.startswith('tag'):
                    line = '#' + line[7:] if line.startswith('hashtag') else '#' + line[3:]
                elif not line.startswith('#') and any(word in line.lower() for word in ['python', 'ml', 'ai', 'data']):
                    # Add # to relevant keywords that should be hashtags
                    line = '#' + line
                
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _generate_fallback_caption(self, job_data: Dict[str, Any], platform: str, config: Dict[str, Any]) -> str:
        
        print(job_data)
        
        """Generate a fallback caption if Gemini fails."""
        title = job_data.get('title', 'Job Opportunity')
        company = job_data.get('company', 'Company')
        location = job_data.get('location', 'Location')
        skills = job_data.get('skills', [])
        apply_url = job_data.get('apply_url', '')
        remote = job_data.get('remote', False)
        
        if platform == 'linkedin':
            caption = f"""🚀 Exciting opportunity alert! 

{title} at {company}
📍 {location}{' 🌍 Remote' if remote else ''}

💼 Skills: {', '.join(skills[:3]) if skills else 'Various'}

Apply now: {apply_url}

#JobOpportunity #TechJobs #CareerGrowth #Hiring"""
        
        else:  # X/Twitter
            caption = f"""🚀 {title} at {company} - {location}{' (Remote)' if remote else ''}

Skills: {', '.join(skills[:2]) if skills else 'Various'}

Apply: {apply_url}

#TechJobs #Hiring"""
        
        return caption
    
    def validate_caption(self, caption: str, platform: str) -> bool:
        """Validate caption meets platform requirements."""
        platform_config = self.caption_configs.get(platform, {})
        max_length = platform_config.get('max_length', 280)
        
        if len(caption) > max_length:
            logger.warning(f"{platform} caption exceeds {max_length} characters: {len(caption)}")
            return False
        
        # Check for required elements
        if platform == 'linkedin':
            if not caption.count('#') >= platform_config.get('hashtag_count', 4):
                logger.warning(f"LinkedIn caption missing required hashtags")
                return False
        
        elif platform == 'x':
            if not caption.count('#') >= platform_config.get('hashtag_count', 2):
                logger.warning(f"X caption missing required hashtags")
                return False
        
        return True
    
    def optimize_caption(self, caption: str, platform: str) -> str:
        """Optimize caption for better engagement."""
        # Add emojis for visual appeal
        emojis = {
            'linkedin': ['🚀', '💼', '📍', '🌟', '🔥'],
            'x': ['🚀', '💼', '📍', '🔥']
        }
        
        platform_emojis = emojis.get(platform, [])
        
        # Add emojis to key sections
        lines = caption.split('\n')
        optimized_lines = []
        
        for i, line in enumerate(lines):
            if i == 0 and platform_emojis:  # Title line
                line = f"{platform_emojis[0]} {line}"
            elif 'location' in line.lower() and len(platform_emojis) > 1:
                line = f"{platform_emojis[1]} {line}"
            elif 'skills' in line.lower() and len(platform_emojis) > 2:
                line = f"{platform_emojis[2]} {line}"
            elif 'apply' in line.lower() and len(platform_emojis) > 3:
                line = f"{platform_emojis[3]} {line}"
            
            optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
