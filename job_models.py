"""
Job data models and normalization utilities.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import re
from fuzzywuzzy import fuzz
from loguru import logger

@dataclass
class Job:
    """Standardized job object."""
    source: str
    source_job_id: str
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    apply_url: str
    skills: List[str]
    seniority: Optional[str]
    remote: bool
    created_at: datetime
    employment_type: Optional[str] = None

class JobNormalizer:
    """Normalizes job data from various sources to standard format."""
    
    # Common skill keywords
    SKILL_KEYWORDS = {
        'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
        'machine_learning': ['machine learning', 'ml', 'ai', 'artificial intelligence', 'deep learning'],
        'data_science': ['data science', 'data scientist', 'analytics', 'statistics'],
        'nlp': ['nlp', 'natural language processing', 'text mining', 'computational linguistics'],
        'web_development': ['web development', 'frontend', 'backend', 'full stack', 'react', 'angular', 'vue'],
        'data_engineering': ['data engineering', 'etl', 'data pipeline', 'big data', 'hadoop', 'spark'],
        'software_engineering': ['software engineering', 'software development', 'programming', 'coding'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud computing', 'docker', 'kubernetes'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'database'],
        'devops': ['devops', 'ci/cd', 'jenkins', 'git', 'terraform', 'ansible']
    }
    
    # Seniority indicators
    SENIORITY_INDICATORS = {
        'fresher': ['fresher', 'entry level', 'junior', '0-1 years', '0-2 years'],
        'junior': ['junior', '1-3 years', '2-4 years', 'associate'],
        'mid': ['mid level', '3-5 years', '4-6 years', 'intermediate'],
        'senior': ['senior', '5+ years', '6+ years', 'lead', 'principal'],
        'expert': ['expert', '8+ years', '10+ years', 'architect', 'staff']
    }
    
    # Remote work indicators
    REMOTE_INDICATORS = [
        'remote', 'work from home', 'wfh', 'virtual', 'telecommute',
        'distributed', 'anywhere', 'flexible location'
    ]
    
    def __init__(self):
        """Initialize the normalizer."""
        self.skill_patterns = self._build_skill_patterns()
    
    def _build_skill_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for skill detection."""
        patterns = {}
        for skill_category, keywords in self.SKILL_KEYWORDS.items():
            # Create pattern that matches any of the keywords
            pattern_str = r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b'
            patterns[skill_category] = re.compile(pattern_str, re.IGNORECASE)
        return patterns
    
    def normalize_job(self, raw_job: Dict[str, Any], source: str) -> Optional[Job]:
        """Normalize a raw job to standard format."""
        try:
            # Extract basic fields
            source_job_id = str(raw_job.get('id', raw_job.get('job_id', '')))
            title = self._extract_title(raw_job)
            company = self._extract_company(raw_job)
            location = self._extract_location(raw_job)
            description = self._extract_description(raw_job)
            apply_url = self._extract_apply_url(raw_job)
            employment_type = self._extract_employment_type(raw_job)
            
            # Extract and analyze skills
            skills = self._extract_skills(title, description)
            
            # Determine seniority
            seniority = self._determine_seniority(title, description)
            
            # Check if remote
            remote = self._is_remote(title, description, location)
            
            # Extract creation date
            created_at = self._extract_created_at(raw_job)
            
            # Validate required fields
            if not all([source_job_id, title, company, apply_url]):
                logger.warning(f"Skipping job with missing required fields: {title}")
                return None
            
            return Job(
                source=source,
                source_job_id=source_job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                apply_url=apply_url,
                skills=skills,
                seniority=seniority,
                remote=remote,
                created_at=created_at,
                employment_type=employment_type
            )
            
        except Exception as e:
            logger.error(f"Error normalizing job from {source}: {e}")
            return None
    
    def _extract_title(self, raw_job: Dict[str, Any]) -> str:
        """Extract job title from raw data."""
        title_fields = ['title', 'job_title', 'position', 'role']
        for field in title_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return ""
    
    def _extract_company(self, raw_job: Dict[str, Any]) -> str:
        """Extract company name from raw data."""
        company_fields = ['company', 'company_name', 'employer', 'organization']
        for field in company_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return ""
    
    def _extract_location(self, raw_job: Dict[str, Any]) -> str:
        """Extract job location from raw data."""
        location_fields = ['location', 'city', 'place', 'address']
        for field in location_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return ""
    
    def _extract_description(self, raw_job: Dict[str, Any]) -> Optional[str]:
        """Extract job description from raw data."""
        desc_fields = ['description', 'summary', 'details', 'requirements']
        for field in desc_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return None
    
    def _extract_apply_url(self, raw_job: Dict[str, Any]) -> str:
        """Extract application URL from raw data."""
        url_fields = ['apply_url', 'url', 'link', 'application_url', 'apply_link']
        for field in url_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return ""
    
    def _extract_employment_type(self, raw_job: Dict[str, Any]) -> Optional[str]:
        """Extract employment type from raw data."""
        type_fields = ['employment_type', 'type', 'contract_type', 'work_type']
        for field in type_fields:
            if raw_job.get(field):
                return str(raw_job[field]).strip()
        return None
    
    def _extract_skills(self, title: str, description: Optional[str]) -> List[str]:
        """Extract skills from title and description."""
        skills = set()
        text_to_analyze = f"{title} {description or ''}".lower()
        
        # Check each skill category
        for skill_category, pattern in self.skill_patterns.items():
            if pattern.search(text_to_analyze):
                skills.add(skill_category)
        
        return list(skills)
    
    def _determine_seniority(self, title: str, description: Optional[str]) -> Optional[str]:
        """Determine job seniority level."""
        text_to_analyze = f"{title} {description or ''}".lower()
        
        for level, indicators in self.SENIORITY_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in text_to_analyze:
                    return level
        
        return None
    
    def _is_remote(self, title: str, description: Optional[str], location: str) -> bool:
        """Determine if job is remote."""
        text_to_analyze = f"{title} {description or ''} {location}".lower()
        
        for indicator in self.REMOTE_INDICATORS:
            if indicator.lower() in text_to_analyze:
                return True
        
        return False
    
    def _extract_created_at(self, raw_job: Dict[str, Any]) -> datetime:
        """Extract job creation date from raw data."""
        date_fields = ['created_at', 'posted_at', 'date', 'timestamp']
        
        for field in date_fields:
            if raw_job.get(field):
                try:
                    # Try to parse various date formats
                    date_value = raw_job[field]
                    if isinstance(date_value, str):
                        # Common date formats
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                            try:
                                return datetime.strptime(date_value, fmt)
                            except ValueError:
                                continue
                    elif isinstance(date_value, (int, float)):
                        # Unix timestamp
                        return datetime.fromtimestamp(date_value)
                except Exception:
                    continue
        
        # Default to current time if no valid date found
        return datetime.utcnow()

def is_duplicate_job(job1: Job, job2: Job, threshold: float = 0.8) -> bool:
    """Check if two jobs are duplicates using fuzzy matching."""
    # Exact match on key fields
    if (job1.company.lower() == job2.company.lower() and
        job1.title.lower() == job2.title.lower() and
        job1.location.lower() == job2.location.lower()):
        return True
    
    # Fuzzy match on title
    title_similarity = fuzz.token_sort_ratio(job1.title.lower(), job2.title.lower()) / 100.0
    if title_similarity > threshold:
        # Additional checks for company and location
        company_similarity = fuzz.ratio(job1.company.lower(), job2.company.lower()) / 100.0
        location_similarity = fuzz.ratio(job1.location.lower(), job2.location.lower()) / 100.0
        
        if company_similarity > 0.7 and location_similarity > 0.7:
            return True
    
    return False

