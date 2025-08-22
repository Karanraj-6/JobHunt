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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

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
        """Fetch jobs from Jooble using POST method."""
        jobs = []
        
        for keyword in keywords:
            try:
                # Jooble API expects POST with JSON payload
                payload = {
                    'keywords': keyword,
                    'location': location,
                    'page': 1
                }
                
                # Use POST method with JSON payload
                response = self.session.post(
                    f'https://jooble.org/api/{self.api_key}',
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if 'jobs' in data:
                    jobs.extend(data['jobs'])
                
                logger.info(f"Fetched {len(data.get('jobs', []))} Jooble jobs for keyword: {keyword}")
                
            except Exception as e:
                logger.error(f"Error fetching Jooble jobs for keyword {keyword}: {e}")
                continue
        
        return jobs

class JobFetcherManager:
    """Manages multiple job fetchers."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize with configuration file path."""
        self.config_path = config_path
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.fetchers = {}
        self._initialize_fetchers()
    
    def _initialize_fetchers(self):
        """Initialize only enabled job fetchers."""
        job_sources = self.config.get('job_sources', {})
        
        # Initialize RapidAPI fetcher only if enabled
        rapidapi_config = job_sources.get('rapidapi', {})
        if rapidapi_config.get('enabled', False) and os.getenv('RAPIDAPI_KEY'):
            try:
                self.fetchers['rapidapi'] = RapidAPIFetcher(self.config)
                logger.info("RapidAPI fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RapidAPI fetcher: {e}")
        
        # Initialize Jooble fetcher only if enabled
        aggregators_config = job_sources.get('aggregators', {})
        if aggregators_config.get('jooble', {}).get('enabled', False) and os.getenv('JOOBLE_API_KEY'):
            try:
                self.fetchers['jooble'] = JoobleFetcher(self.config)
                logger.info("Jooble fetcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Jooble fetcher: {e}")
        
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
                
                elif source_name == 'jooble':
                    # Handle Jooble
                    aggregators_config = self.config['job_sources']['aggregators']
                    if aggregators_config.get('jooble', {}).get('enabled', False):
                        jooble_jobs = fetcher.fetch_jobs(
                            keywords=aggregators_config['jooble']['keywords'],
                            max_results=aggregators_config['jooble']['max_results']
                        )
                        all_jobs['jooble'] = jooble_jobs
                
            except Exception as e:
                logger.error(f"Error fetching jobs from {source_name}: {e}")
                continue
        
        return all_jobs
    
    def get_fetcher(self, source_name: str) -> Optional[BaseJobFetcher]:
        """Get a specific fetcher by name."""
        return self.fetchers.get(source_name)
    
    def list_enabled_sources(self) -> List[str]:
        """List all enabled job sources."""
        return list(self.fetchers.keys())

