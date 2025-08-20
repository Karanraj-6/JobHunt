"""
Job processing, filtering, and deduplication.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger
import yaml

from models import JobsRaw, JobsClean
from job_models import Job, JobNormalizer, is_duplicate_job
from database import get_db

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
        """Check if seniority passes the filter."""
        excluded_seniority = self.filters.get('excluded_seniority', [])
        preferred_seniority = self.filters.get('preferred_seniority', [])
        
        # If no seniority specified, pass through
        if not seniority:
            return True
        
        # Check excluded seniority
        if seniority.lower() in [level.lower() for level in excluded_seniority]:
            return False
        
        # If preferred seniority is specified, check if job matches
        if preferred_seniority:
            return seniority.lower() in [level.lower() for level in preferred_seniority]
        
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
        """Store raw jobs in the database."""
        db = get_db()
        
        try:
            for source, jobs in raw_jobs.items():
                for raw_job in jobs:
                    try:
                        # Check if job already exists
                        existing = db.query(JobsRaw).filter(
                            JobsRaw.source == source,
                            JobsRaw.payload.contains(raw_job)
                        ).first()
                        
                        if not existing:
                            db_job = JobsRaw(
                                source=source,
                                fetched_at=datetime.utcnow(),
                                payload=raw_job
                            )
                            db.add(db_job)
                    
                    except Exception as e:
                        logger.error(f"Error storing raw job from {source}: {e}")
                        continue
            
            db.commit()
            logger.info("Raw jobs stored successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing raw jobs: {e}")
            raise
        finally:
            db.close()
    
    def store_clean_jobs(self, jobs: List[Job]) -> List[str]:
        """Store clean jobs in the database and return their IDs."""
        db = get_db()
        stored_job_ids = []
        
        try:
            for job in jobs:
                try:
                    # Check if job already exists
                    existing = db.query(JobsClean).filter(
                        JobsClean.source_job_id == job.source_job_id,
                        JobsClean.source == job.source
                    ).first()
                    
                    if existing:
                        # Update existing job
                        existing.title = job.title
                        existing.company = job.company
                        existing.location = job.location
                        existing.description = job.description
                        existing.apply_url = job.apply_url
                        existing.skills = job.skills
                        existing.seniority = job.seniority
                        existing.remote = job.remote
                        existing.employment_type = job.employment_type
                        stored_job_ids.append(str(existing.id))
                    else:
                        # Create new job
                        db_job = JobsClean(
                            source_job_id=job.source_job_id,
                            title=job.title,
                            company=job.company,
                            location=job.location,
                            description=job.description,
                            apply_url=job.apply_url,
                            skills=job.skills,
                            seniority=job.seniority,
                            remote=job.remote,
                            employment_type=job.employment_type,
                            created_at=job.created_at
                        )
                        db.add(db_job)
                        db.flush()  # Get the ID
                        stored_job_ids.append(str(db_job.id))
                
                except Exception as e:
                    logger.error(f"Error storing clean job {job.title}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Successfully stored {len(stored_job_ids)} clean jobs")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing clean jobs: {e}")
            raise
        finally:
            db.close()
        
        return stored_job_ids
    
    def get_existing_jobs(self) -> List[Job]:
        """Get existing clean jobs from the database."""
        db = get_db()
        
        try:
            db_jobs = db.query(JobsClean).all()
            
            jobs = []
            for db_job in db_jobs:
                job = Job(
                    source=db_job.source_job_id,  # Note: this should be the source, not source_job_id
                    source_job_id=db_job.source_job_id,
                    title=db_job.title,
                    company=db_job.company,
                    location=db_job.location,
                    description=db_job.description,
                    apply_url=db_job.apply_url,
                    skills=db_job.skills or [],
                    seniority=db_job.seniority,
                    remote=db_job.remote,
                    created_at=db_job.created_at,
                    employment_type=db_job.employment_type
                )
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error retrieving existing jobs: {e}")
            return []
        finally:
            db.close()
    
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

