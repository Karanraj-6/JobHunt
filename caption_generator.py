"""
Caption generation using Gemini API for social media posts.
Generates engaging captions for LinkedIn and X (Twitter) job postings.
"""

import os
import re
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from loguru import logger
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
    
    def generate_captions(self, job_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate captions for all platforms."""
        captions = {}
        
        platforms = self.posting_config.get('platforms', ['linkedin', 'x'])
        
        for platform in platforms:
            try:
                caption = self._generate_platform_caption(job_data, platform)
                if caption:
                    captions[platform] = caption
                    logger.info(f"Generated {platform} caption for job: {job_data.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error generating {platform} caption: {e}")
                continue
        
        return captions
    
    def _generate_platform_caption(self, job_data: Dict[str, Any], platform: str) -> Optional[str]:
        """Generate caption for a specific platform."""
        platform_config = self.caption_configs.get(platform, {})
        
        if platform == 'linkedin':
            return self._generate_linkedin_caption(job_data, platform_config)
        elif platform == 'x':
            return self._generate_x_caption(job_data, platform_config)
        else:
            logger.warning(f"Unsupported platform: {platform}")
            return None
    
    def _generate_linkedin_caption(self, job_data: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
        """Generate LinkedIn caption."""
        prompt = self._build_linkedin_prompt(job_data, config)
        
        try:
            return self._generate_with_gemini(prompt, config)
        except Exception as e:
            logger.error(f"Error generating LinkedIn caption with Gemini: {e}")
            return self._generate_fallback_caption(job_data, 'linkedin', config)
    
    def _generate_x_caption(self, job_data: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
        """Generate X (Twitter) caption."""
        prompt = self._build_x_prompt(job_data, config)
        
        try:
            return self._generate_with_gemini(prompt, config)
        except Exception as e:
            logger.error(f"Error generating X caption with Gemini: {e}")
            return self._generate_fallback_caption(job_data, 'x', config)
    
    def _build_linkedin_prompt(self, job_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build LinkedIn prompt."""
        max_length = config.get('max_length', 1300)
        hashtag_count = config.get('hashtag_count', 4)
        tone = config.get('tone', 'professional')
        audience = config.get('audience', 'Indian tech professionals')
        
        prompt = f"""You are a concise social media assistant. Generate a professional LinkedIn post for this job:

Title: {job_data.get('title', 'N/A')}
Company: {job_data.get('company', 'N/A')}
Location: {job_data.get('location', 'N/A')}
Skills: {', '.join(job_data.get('skills', []))}
Remote: {'Yes' if job_data.get('remote', False) else 'No'}
Link: {job_data.get('apply_url', 'N/A')}

Constraints:
- Maximum {max_length} characters
- {hashtag_count} relevant hashtags
- {tone} tone
- Target audience: {audience}
- Include the apply link
- Make it engaging but not overly promotional
- Focus on the opportunity and company

Format: Write the post content followed by hashtags on new lines."""
        
        return prompt
    
    def _build_x_prompt(self, job_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build X (Twitter) prompt."""
        max_length = config.get('max_length', 280)
        hashtag_count = config.get('hashtag_count', 2)
        tone = config.get('tone', 'casual')
        audience = config.get('audience', 'tech community')
        
        prompt = f"""Create a tweet (maximum {max_length} characters) about this job. Include {hashtag_count} hashtags and the link. Keep it readable and engaging.

Job details:
Title: {job_data.get('title', 'N/A')}
Company: {job_data.get('company', 'N/A')}
Location: {job_data.get('location', 'N/A')}
Skills: {', '.join(job_data.get('skills', []))}
Remote: {'Yes' if job_data.get('remote', False) else 'No'}
Link: {job_data.get('apply_url', 'N/A')}

Tone: {tone}
Audience: {audience}

Requirements:
- Include the apply link
- Use {hashtag_count} relevant hashtags
- Make it engaging and shareable
- Stay within character limit"""
        
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
