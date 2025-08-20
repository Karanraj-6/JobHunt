"""
Job fetchers for various job sources.
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import yaml

class BaseJobFetcher:
    """Base class for job fetchers."""
    
    def __init__(self, config: dict):
        """Initialize with configuration."""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    def fetch_jobs(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch jobs from the source. Override in subclasses."""
        raise NotImplementedError

class RapidAPIFetcher(BaseJobFetcher):
    """Fetcher for RapidAPI job endpoints."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is required")
        
        self.session.headers.update({
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        })
    
    def fetch_indeed_jobs(self, keywords: List[str], location: str = "India", max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from Indeed via RapidAPI."""
        jobs = []
        
        for keyword in keywords:
            try:
                params = {
                    'query': keyword,
                    'page': '1',
                    'num_pages': '1',
                    'country': 'in',
                    'location': location
                }
                
                response = self._make_request(
                    'https://jsearch.p.rapidapi.com/search',
                    params=params
                )
                
                if 'data' in response:
                    jobs.extend(response['data'][:max_results // len(keywords)])
                
                logger.info(f"Fetched {len(response.get('data', []))} Indeed jobs for keyword: {keyword}")
                
            except Exception as e:
                logger.error(f"Error fetching Indeed jobs for keyword {keyword}: {e}")
                continue
        
        return jobs
    
    def fetch_naukri_jobs(self, keywords: List[str], location: str = "India", max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from Naukri via RapidAPI."""
        # Note: This is a placeholder. Naukri might not be available on RapidAPI
        # You might need to use their official API or web scraping
        logger.warning("Naukri jobs fetching not implemented - requires official API access")
        return []
    
    def fetch_linkedin_jobs(self, keywords: List[str], location: str = "India", max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from LinkedIn Jobs via RapidAPI."""
        # Note: This is a placeholder. LinkedIn Jobs might not be available on RapidAPI
        logger.warning("LinkedIn Jobs fetching not implemented - requires official API access")
        return []

class JoobleFetcher(BaseJobFetcher):
    """Fetcher for Jooble job aggregator."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('JOOBLE_API_KEY')
        if not self.api_key:
            raise ValueError("JOOBLE_API_KEY environment variable is required")
    
    def fetch_jobs(self, keywords: List[str], location: str = "India", max_results: int = 200) -> List[Dict[str, Any]]:
        """Fetch jobs from Jooble."""
        jobs = []
        
        for keyword in keywords:
            try:
                params = {
                    'keywords': keyword,
                    'location': location,
                    'limit': min(max_results // len(keywords), 50)  # Jooble limit per request
                }
                
                response = self._make_request(
                    'https://jooble.org/api/',
                    params=params,
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                
                if 'jobs' in response:
                    jobs.extend(response['jobs'])
                
                logger.info(f"Fetched {len(response.get('jobs', []))} Jooble jobs for keyword: {keyword}")
                
            except Exception as e:
                logger.error(f"Error fetching Jooble jobs for keyword {keyword}: {e}")
                continue
        
        return jobs

class AdzunaFetcher(BaseJobFetcher):
    """Fetcher for Adzuna job aggregator."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.app_id = os.getenv('ADZUNA_APP_ID')
        self.app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables are required")
    
    def fetch_jobs(self, keywords: List[str], location: str = "India", max_results: int = 200) -> List[Dict[str, Any]]:
        """Fetch jobs from Adzuna."""
        jobs = []
        
        for keyword in keywords:
            try:
                params = {
                    'app_id': self.app_id,
                    'app_key': self.app_key,
                    'what': keyword,
                    'where': location,
                    'results_per_page': min(max_results // len(keywords), 50)
                }
                
                response = self._make_request(
                    'https://api.adzuna.com/v1/api/jobs/in/search/1',
                    params=params
                )
                
                if 'results' in response:
                    jobs.extend(response['results'])
                
                logger.info(f"Fetched {len(response.get('results', []))} Adzuna jobs for keyword: {keyword}")
                
            except Exception as e:
                logger.error(f"Error fetching Adzuna jobs for keyword {keyword}: {e}")
                continue
        
        return jobs

class GreenhouseFetcher(BaseJobFetcher):
    """Fetcher for Greenhouse ATS."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('GREENHOUSE_API_KEY')
        if not self.api_key:
            raise ValueError("GREENHOUSE_API_KEY environment variable is required")
        
        self.session.headers.update({
            'Authorization': f'Basic {self.api_key}'
        })
    
    def fetch_jobs(self, company_ids: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from Greenhouse companies."""
        jobs = []
        
        for company_id in company_ids:
            try:
                response = self._make_request(
                    f'https://boards-api.greenhouse.io/v1/boards/{company_id}/jobs'
                )
                
                if 'jobs' in response:
                    company_jobs = response['jobs'][:max_results // len(company_ids)]
                    for job in company_jobs:
                        job['company_id'] = company_id
                    jobs.extend(company_jobs)
                
                logger.info(f"Fetched {len(response.get('jobs', []))} Greenhouse jobs for company: {company_id}")
                
            except Exception as e:
                logger.error(f"Error fetching Greenhouse jobs for company {company_id}: {e}")
                continue
        
        return jobs

class LeverFetcher(BaseJobFetcher):
    """Fetcher for Lever ATS."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('LEVER_API_KEY')
        if not self.api_key:
            raise ValueError("LEVER_API_KEY environment variable is required")
    
    def fetch_jobs(self, company_ids: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from Lever companies."""
        jobs = []
        
        for company_id in company_ids:
            try:
                response = self._make_request(
                    f'https://api.lever.co/v0/postings/{company_id}',
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                
                company_jobs = response[:max_results // len(company_ids)]
                for job in company_jobs:
                    job['company_id'] = company_id
                jobs.extend(company_jobs)
                
                logger.info(f"Fetched {len(response)} Lever jobs for company: {company_id}")
                
            except Exception as e:
                logger.error(f"Error fetching Lever jobs for company {company_id}: {e}")
                continue
        
        return jobs

class SmartRecruitersFetcher(BaseJobFetcher):
    """Fetcher for SmartRecruiters ATS."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('SMARTRECRUITERS_API_KEY')
        if not self.api_key:
            raise ValueError("SMARTRECRUITERS_API_KEY environment variable is required")
    
    def fetch_jobs(self, company_ids: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from SmartRecruiters companies."""
        jobs = []
        
        for company_id in company_ids:
            try:
                response = self._make_request(
                    f'https://api.smartrecruiters.com/v1/companies/{company_id}/postings',
                    headers={'X-SmartToken': self.api_key}
                )
                
                if 'content' in response:
                    company_jobs = response['content'][:max_results // len(company_ids)]
                    for job in company_jobs:
                        job['company_id'] = company_id
                    jobs.extend(company_jobs)
                
                logger.info(f"Fetched {len(response.get('content', []))} SmartRecruiters jobs for company: {company_id}")
                
            except Exception as e:
                logger.error(f"Error fetching SmartRecruiters jobs for company {company_id}: {e}")
                continue
        
        return jobs

class WorkdayFetcher(BaseJobFetcher):
    """Fetcher for Workday ATS."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = os.getenv('WORKDAY_API_KEY')
        if not self.api_key:
            raise ValueError("WORKDAY_API_KEY environment variable is required")
    
    def fetch_jobs(self, company_sites: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch jobs from Workday companies."""
        # Note: Workday API implementation depends on specific company setup
        # This is a placeholder for the basic structure
        logger.warning("Workday jobs fetching not fully implemented - requires company-specific setup")
        return []

class JobFetcherManager:
    """Manages all job fetchers and coordinates fetching."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the job fetcher manager."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.fetchers = {}
        self._initialize_fetchers()
    
    def _initialize_fetchers(self):
        """Initialize all enabled job fetchers."""
        job_sources = self.config.get('job_sources', {})
        
        # Initialize RapidAPI fetcher
        if job_sources.get('rapidapi', {}).get('enabled', False):
            try:
                self.fetchers['rapidapi'] = RapidAPIFetcher(self.config)
                logger.info("RapidAPI fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RapidAPI fetcher: {e}")
        
        # Initialize ATS fetchers
        ats_config = job_sources.get('ats', {})
        if ats_config.get('greenhouse', {}).get('enabled', False):
            try:
                self.fetchers['greenhouse'] = GreenhouseFetcher(self.config)
                logger.info("Greenhouse fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Greenhouse fetcher: {e}")
        
        if ats_config.get('lever', {}).get('enabled', False):
            try:
                self.fetchers['lever'] = LeverFetcher(self.config)
                logger.info("Lever fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Lever fetcher: {e}")
        
        if ats_config.get('smartrecruiters', {}).get('enabled', False):
            try:
                self.fetchers['smartrecruiters'] = SmartRecruitersFetcher(self.config)
                logger.info("SmartRecruiters fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SmartRecruiters fetcher: {e}")
        
        if ats_config.get('workday', {}).get('enabled', False):
            try:
                self.fetchers['workday'] = WorkdayFetcher(self.config)
                logger.info("Workday fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Workday fetcher: {e}")
        
        # Initialize aggregator fetchers
        aggregators_config = job_sources.get('aggregators', {})
        if aggregators_config.get('jooble', {}).get('enabled', False):
            try:
                self.fetchers['jooble'] = JoobleFetcher(self.config)
                logger.info("Jooble fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Jooble fetcher: {e}")
        
        if aggregators_config.get('adzuna', {}).get('enabled', False):
            try:
                self.fetchers['adzuna'] = AdzunaFetcher(self.config)
                logger.info("Adzuna fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Adzuna fetcher: {e}")
        
        logger.info(f"Initialized {len(self.fetchers)} job fetchers")
    
    def fetch_all_jobs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch jobs from all enabled sources."""
        all_jobs = {}
        
        for source_name, fetcher in self.fetchers.items():
            try:
                if source_name == 'rapidapi':
                    # Handle RapidAPI sources separately
                    rapidapi_config = self.config['job_sources']['rapidapi']
                    jobs = []
                    
                    if rapidapi_config.get('indeed', {}).get('enabled', False):
                        indeed_jobs = fetcher.fetch_indeed_jobs(
                            keywords=rapidapi_config['indeed']['keywords'],
                            max_results=rapidapi_config['indeed']['max_results']
                        )
                        jobs.extend(indeed_jobs)
                    
                    if rapidapi_config.get('naukri', {}).get('enabled', False):
                        naukri_jobs = fetcher.fetch_naukri_jobs(
                            keywords=rapidapi_config['naukri']['keywords'],
                            max_results=rapidapi_config['naukri']['max_results']
                        )
                        jobs.extend(naukri_jobs)
                    
                    if rapidapi_config.get('linkedin_jobs', {}).get('enabled', False):
                        linkedin_jobs = fetcher.fetch_linkedin_jobs(
                            keywords=rapidapi_config['linkedin_jobs']['keywords'],
                            max_results=rapidapi_config['linkedin_jobs']['max_results']
                        )
                        jobs.extend(linkedin_jobs)
                    
                    all_jobs['rapidapi'] = jobs
                
                elif source_name in ['greenhouse', 'lever', 'smartrecruiters', 'workday']:
                    # ATS sources
                    ats_config = self.config['job_sources']['ats'][source_name]
                    if ats_config.get('enabled', False):
                        jobs = fetcher.fetch_jobs(
                            company_ids=ats_config['companies'],
                            max_results=ats_config.get('max_results', 100)
                        )
                        all_jobs[source_name] = jobs
                
                elif source_name in ['jooble', 'adzuna']:
                    # Aggregator sources
                    agg_config = self.config['job_sources']['aggregators'][source_name]
                    if agg_config.get('enabled', False):
                        jobs = fetcher.fetch_jobs(
                            keywords=self.config['job_filters']['required_skills'],
                            max_results=agg_config['max_results']
                        )
                        all_jobs[source_name] = jobs
                
            except Exception as e:
                logger.error(f"Error fetching jobs from {source_name}: {e}")
                all_jobs[source_name] = []
        
        return all_jobs

