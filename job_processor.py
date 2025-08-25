"""
Job processing, normalization, and storage management.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from database import get_db
from job_models import Job, JobNormalizer, is_duplicate_job

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

class JobProcessor:
    """Handles job processing, filtering, and storage."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the job processor."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.normalizer = JobNormalizer()
        self.filters = self.config.get('job_filters', {})
    
    def process_raw_jobs(self, raw_jobs: Dict[str, List[Dict[str, Any]]]) -> List[Job]:
        """Process raw jobs from all sources."""
        all_normalized_jobs = []
        
        for source, jobs in raw_jobs.items():
            logger.info(f"Processing {len(jobs)} jobs from {source}")
            
            for raw_job in jobs:
                try:
                    normalized_job = self.normalizer.normalize_job(raw_job, source)
                    if normalized_job:
                        all_normalized_jobs.append(normalized_job)
                except Exception as e:
                    logger.error(f"Error normalizing job from {source}: {e}")
                    continue
        
        logger.info(f"Successfully normalized {len(all_normalized_jobs)} jobs")
        return all_normalized_jobs
    
    def filter_jobs(self, jobs: List[Job]) -> List[Job]:
        """Filter jobs based on configuration rules."""
        filtered_jobs = []
        
        for job in jobs:
            if self._passes_filters(job):
                filtered_jobs.append(job)
        
        logger.info(f"Filtered {len(jobs)} jobs down to {len(filtered_jobs)}")
        return filtered_jobs
    
    def _passes_filters(self, job: Job) -> bool:
        """Check if a job passes all filters."""
        # Location filter
        if not self._passes_location_filter(job.location):
            return False
        
        # Skills filter
        if not self._passes_skills_filter(job.skills):
            return False
        
        # Seniority filter
        if not self._passes_seniority_filter(job.seniority):
            return False
        
        # Job title filter (ensure it's entry-level)
        if not self._passes_job_title_filter(job.title):
            return False
        
        # Experience filter (check description for experience requirements)
        if not self._passes_experience_filter(job.description, job.seniority):
            return False
        
        return True
    
    def _passes_location_filter(self, location: str) -> bool:
        """Check if location passes the filter."""
        allowed_locations = self.filters.get('allowed_locations', [])
        
        if not allowed_locations:
            return True  # No location restrictions
        
        location_lower = location.lower()
        for allowed in allowed_locations:
            if allowed.lower() in location_lower:
                return True
        
        return False
    
    def _passes_skills_filter(self, skills: List[str]) -> bool:
        """Check if skills pass the filter."""
        required_skills = self.filters.get('required_skills', [])
        
        if not required_skills:
            return True  # No skill restrictions
        
        if not skills:
            return False  # Job has no skills identified
        
        # Check if at least one required skill is present
        for required in required_skills:
            if required.lower() in [skill.lower() for skill in skills]:
                return True
        
        return False
    
    def _passes_seniority_filter(self, seniority: Optional[str]) -> bool:
        """Check if seniority passes the filter - only allow entry-level positions."""
        excluded_seniority = self.filters.get('excluded_seniority', [])
        preferred_seniority = self.filters.get('preferred_seniority', [])
        
        # If no seniority specified, be more flexible - allow through for further filtering
        if not seniority:
            return True  # Allow jobs without seniority info to pass through
        
        seniority_lower = seniority.lower()
        
        # Check excluded seniority (reject all senior positions)
        for excluded in excluded_seniority:
            if excluded.lower() in seniority_lower:
                logger.debug(f"Rejected job with excluded seniority: {seniority}")
                return False
        
        # Check preferred seniority (only allow entry-level positions)
        if preferred_seniority:
            for preferred in preferred_seniority:
                if preferred.lower() in seniority_lower:
                    logger.debug(f"Accepted job with preferred seniority: {seniority}")
                    return True
        
        # Additional checks for experience years (0-2 years only)
        experience_patterns = [
            r'(\d+)[\+-]?\s*years?',  # e.g., "2+ years", "1-2 years"
            r'(\d+)\s*to\s*(\d+)\s*years?',  # e.g., "1 to 2 years"
            r'less\s*than\s*(\d+)\s*years?',  # e.g., "less than 2 years"
            r'upto\s*(\d+)\s*years?',  # e.g., "upto 2 years"
            r'max\s*(\d+)\s*years?',  # e.g., "max 2 years"
        ]
        
        for pattern in experience_patterns:
            import re
            match = re.search(pattern, seniority_lower)
            if match:
                try:
                    years = int(match.group(1))
                    if years <= 2:
                        logger.debug(f"Accepted job with acceptable experience: {seniority} ({years} years)")
                        return True
                    else:
                        logger.debug(f"Rejected job with too much experience: {seniority} ({years} years)")
                        return False
                except (ValueError, IndexError):
                    continue
        
        # If we reach here, the seniority doesn't match our criteria
        logger.debug(f"Rejected job with unclear seniority: {seniority}")
        return False
    
    def _passes_job_title_filter(self, title: str) -> bool:
        """Check if job title indicates entry-level position."""
        if not title:
            return False
        
        title_lower = title.lower()
        
        # Entry-level indicators in job titles
        entry_level_indicators = [
            'fresher', 'junior', 'entry level', 'entry-level', 'associate', 'assistant',
            'trainee', 'intern', 'internship', 'new grad', 'new graduate', 'recent graduate',
            'student', 'apprentice', 'entry', 'beginner', 'junior developer', 'junior engineer',
            'junior analyst', 'junior scientist', 'junior consultant'
        ]
        
        # Check if title contains entry-level indicators
        for indicator in entry_level_indicators:
            if indicator in title_lower:
                logger.debug(f"Accepted job with entry-level title: {title}")
                return True
        
        # Check for experience patterns in title (0-2 years)
        experience_patterns = [
            r'(\d+)[\+-]?\s*years?',  # e.g., "2+ years", "1-2 years"
            r'(\d+)\s*to\s*(\d+)\s*years?',  # e.g., "1 to 2 years"
            r'less\s*than\s*(\d+)\s*years?',  # e.g., "less than 2 years"
            r'upto\s*(\d+)\s*years?',  # e.g., "upto 2 years"
            r'max\s*(\d+)\s*years?',  # e.g., "max 2 years"
        ]
        
        for pattern in experience_patterns:
            import re
            match = re.search(pattern, title_lower)
            if match:
                try:
                    years = int(match.group(1))
                    if years <= 2:
                        logger.debug(f"Accepted job with acceptable experience in title: {title} ({years} years)")
                        return True
                    else:
                        logger.debug(f"Rejected job with too much experience in title: {title} ({years} years)")
                        return False
                except (ValueError, IndexError):
                    continue
        
        # If title doesn't clearly indicate entry-level, allow it through (experience filter will handle it)
        logger.debug(f"Allowing job with unclear entry-level title: {title}")
        return True
    
    def _passes_experience_filter(self, description: Optional[str], seniority: Optional[str]) -> bool:
        """Check if job description indicates entry-level experience requirements (0-2 years)."""
        import re
        
        # Combine description and seniority for analysis
        text_to_analyze = ""
        if description:
            text_to_analyze += description.lower()
        if seniority:
            text_to_analyze += " " + seniority.lower()
        
        if not text_to_analyze:
            return True  # If no text to analyze, allow through
        
        # Patterns that indicate entry-level positions (0-2 years)
        entry_level_patterns = [
            r'(\d+)[\+-]?\s*years?\s*experience',  # e.g., "2+ years experience"
            r'(\d+)\s*to\s*(\d+)\s*years?\s*experience',  # e.g., "1 to 2 years experience"
            r'less\s*than\s*(\d+)\s*years?\s*experience',  # e.g., "less than 2 years experience"
            r'upto\s*(\d+)\s*years?\s*experience',  # e.g., "upto 2 years experience"
            r'max\s*(\d+)\s*years?\s*experience',  # e.g., "max 2 years experience"
            r'(\d+)[\+-]?\s*years?\s*of\s*experience',  # e.g., "2+ years of experience"
            r'(\d+)\s*to\s*(\d+)\s*years?\s*of\s*experience',  # e.g., "1 to 2 years of experience"
            r'experience\s*level[:\s]*(\d+)[\+-]?\s*years?',  # e.g., "Experience level: 2+ years"
            r'required\s*experience[:\s]*(\d+)[\+-]?\s*years?',  # e.g., "Required experience: 2+ years"
            r'minimum\s*experience[:\s]*(\d+)[\+-]?\s*years?',  # e.g., "Minimum experience: 2+ years"
        ]
        
        # Check for entry-level experience patterns
        for pattern in entry_level_patterns:
            match = re.search(pattern, text_to_analyze)
            if match:
                try:
                    years = int(match.group(1))
                    if years <= 2:
                        logger.debug(f"Accepted job with acceptable experience requirement: {years} years")
                        return True
                    else:
                        logger.debug(f"Rejected job with too much experience requirement: {years} years")
                        return False
                except (ValueError, IndexError):
                    continue
        
        # Patterns that indicate senior positions (reject these)
        senior_patterns = [
            r'(\d+)[\+-]?\s*years?\s*experience',  # e.g., "5+ years experience"
            r'(\d+)\s*to\s*(\d+)\s*years?\s*experience',  # e.g., "3 to 5 years experience"
            r'minimum\s*(\d+)[\+-]?\s*years?\s*experience',  # e.g., "minimum 3+ years experience"
            r'at\s*least\s*(\d+)[\+-]?\s*years?\s*experience',  # e.g., "at least 3+ years experience"
            r'(\d+)[\+-]?\s*years?\s*of\s*experience',  # e.g., "5+ years of experience"
        ]
        
        # Check for senior experience patterns
        for pattern in senior_patterns:
            match = re.search(pattern, text_to_analyze)
            if match:
                try:
                    years = int(match.group(1))
                    if years > 2:
                        logger.debug(f"Rejected job with senior experience requirement: {years} years")
                        return False
                except (ValueError, IndexError):
                    continue
        
        # Keywords that indicate entry-level positions
        entry_level_keywords = [
            'fresher', 'junior', 'entry level', 'entry-level', 'associate', 'assistant',
            'trainee', 'intern', 'internship', 'new grad', 'new graduate', 'recent graduate',
            'student', 'apprentice', 'entry', 'beginner', 'graduate', 'fresh graduate',
            'no experience', '0 experience', 'zero experience', 'first job', 'first role',
            'entry position', 'junior position', 'associate position', 'trainee position'
        ]
        
        # Check for entry-level keywords
        for keyword in entry_level_keywords:
            if keyword in text_to_analyze:
                logger.debug(f"Accepted job with entry-level keyword: {keyword}")
                return True
        
        # Keywords that indicate senior positions (reject these)
        senior_keywords = [
            'senior', 'lead', 'principal', 'architect', 'manager', 'head', 'chief',
            'staff', 'director', 'vp', 'c-level', 'executive', 'team lead', 'tech lead',
            'engineering manager', 'senior developer', 'senior engineer', 'senior analyst',
            'senior scientist', 'senior consultant', 'experienced', 'expert', 'specialist'
        ]
        
        # Check for senior keywords
        for keyword in senior_keywords:
            if keyword in text_to_analyze:
                logger.debug(f"Rejected job with senior keyword: {keyword}")
                return False
        
        # If we can't determine experience level, allow it through (better to include than exclude)
        logger.debug(f"Could not determine experience level, allowing job through")
        return True
    
    def deduplicate_jobs(self, jobs: List[Job]) -> List[Job]:
        """Remove duplicate jobs using fuzzy matching."""
        if not jobs:
            return []
        
        unique_jobs = [jobs[0]]
        
        for job in jobs[1:]:
            is_duplicate = False
            
            for existing_job in unique_jobs:
                if is_duplicate_job(job, existing_job):
                    is_duplicate = True
                    logger.debug(f"Found duplicate: {job.title} at {job.company}")
                    break
            
            if not is_duplicate:
                unique_jobs.append(job)
        
        logger.info(f"Deduplicated {len(jobs)} jobs down to {len(unique_jobs)}")
        return unique_jobs
    
    def store_raw_jobs(self, raw_jobs: Dict[str, List[Dict[str, Any]]]) -> None:
        """Store raw jobs in MongoDB."""
        dbm = get_db()
        col = dbm.get_collection('jobs_raw')
        for source, jobs in raw_jobs.items():
            for raw_job in jobs:
                try:
                    doc = {
                        'source': source,
                        'fetched_at': datetime.utcnow(),
                        'payload': raw_job
                    }
                    col.insert_one(doc)
                except Exception as e:
                    logger.error(f"Error storing raw job from {source}: {e}")
                    continue
        logger.info("Raw jobs stored successfully")
    
    def store_clean_jobs(self, jobs: List[Job]) -> List[str]:
        """Store clean jobs in MongoDB and return their IDs."""
        dbm = get_db()
        col = dbm.get_collection('jobs_clean')
        stored_job_ids: List[str] = []
        for job in jobs:
            try:
                doc = {
                    'source': job.source,
                    'source_job_id': job.source_job_id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'apply_url': job.apply_url,
                    'skills': job.skills,
                    'seniority': job.seniority,
                    'remote': job.remote,
                    'employment_type': job.employment_type,
                    'created_at': job.created_at,
                }
                res = col.insert_one(doc)
                stored_job_ids.append(str(res.inserted_id))
            except Exception as e:
                logger.error(f"Error storing clean job {job.title}: {e}")
                continue
        logger.info(f"Successfully stored {len(stored_job_ids)} clean jobs")
        return stored_job_ids
    
    def get_existing_jobs(self) -> List[Job]:
        """Get existing clean jobs from MongoDB."""
        dbm = get_db()
        col = dbm.get_collection('jobs_clean')
        jobs: List[Job] = []
        try:
            for doc in col.find({}).limit(2000):
                jobs.append(Job(
                    source=doc.get('source', ''),
                    source_job_id=doc.get('source_job_id', ''),
                    title=doc.get('title', ''),
                    company=doc.get('company', ''),
                    location=doc.get('location', ''),
                    description=doc.get('description'),
                    apply_url=doc.get('apply_url', ''),
                    skills=doc.get('skills', []) or [],
                    seniority=doc.get('seniority'),
                    remote=bool(doc.get('remote', False)),
                    created_at=doc.get('created_at') or datetime.utcnow(),
                    employment_type=doc.get('employment_type')
                ))
            return jobs
        except Exception as e:
            logger.error(f"Error retrieving existing jobs: {e}")
            return []
    
    def process_job_pipeline(self, raw_jobs: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Complete job processing pipeline."""
        logger.info("Starting job processing pipeline")
        
        # Store raw jobs
        self.store_raw_jobs(raw_jobs)
        
        # Normalize jobs
        normalized_jobs = self.process_raw_jobs(raw_jobs)
        
        # Get existing jobs for deduplication
        existing_jobs = self.get_existing_jobs()
        all_jobs = existing_jobs + normalized_jobs
        
        # Deduplicate
        unique_jobs = self.deduplicate_jobs(all_jobs)
        
        # Filter
        filtered_jobs = self.filter_jobs(unique_jobs)
        
        # Store clean jobs
        stored_ids = self.store_clean_jobs(filtered_jobs)
        
        logger.info(f"Job processing pipeline completed. Stored {len(stored_ids)} jobs.")
        return stored_ids

