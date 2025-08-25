"""
Main orchestrator for the job automation application.
"""
import os
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

from database import init_database, get_db, close_database
from job_fetchers import JobFetcherManager
from job_processor import JobProcessor
from caption_generator import CaptionGenerator
from image_generator import ImageGenerationManager
from social_posters import SocialPosterManager

class JobAutomationOrchestrator:
    """Main orchestrator for job automation workflow."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the orchestrator."""
        self.config_path = config_path
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize components
        self._init_components()
        
        # Setup scheduler
        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()
        
        logger.info("Job Automation Orchestrator initialized successfully")
    
    def _init_components(self):
        """Initialize all system components."""
        try:
            # Initialize database
            init_database(self.config_path)
            
            # Initialize job fetchers
            self.job_fetcher_manager = JobFetcherManager(self.config_path)
            
            # Initialize job processor
            self.job_processor = JobProcessor(self.config_path)
            
            # Initialize caption generator
            self.caption_generator = CaptionGenerator(self.config_path)
            
            # Initialize image generation manager
            self.image_generation_manager = ImageGenerationManager(self.config_path)
            
            # Initialize social media posters
            self.social_poster_manager = SocialPosterManager(self.config_path)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _setup_scheduler(self):
        """Setup the job scheduler."""
        try:
            timezone = pytz.timezone(self.config.get('TIMEZONE', 'Asia/Kolkata'))
            
            # Job fetching schedule (every 6 hours)
            self.scheduler.add_job(
                func=self.fetch_and_process_jobs,
                trigger=CronTrigger(hour='*/6', timezone=timezone),
                id='fetch_jobs',
                name='Fetch and Process Jobs',
                max_instances=1
            )
            
            # Social media posting schedule
            posting_config = self.config.get('posting', {})
            platforms = posting_config.get('platforms', [])
            
            for platform in platforms:
                if platform in posting_config.get('schedule', {}):
                    schedule_times = posting_config['schedule'][platform]
                    for time_str in schedule_times:
                        hour, minute = map(int, time_str.split(':'))
                        self.scheduler.add_job(
                            func=self.post_pending_content,
                            trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
                            id=f'post_{platform}_{time_str}',
                            name=f'Post to {platform} at {time_str}',
                            max_instances=1,
                            kwargs={'platform': platform}
                        )
            
            # Analytics collection schedule (every 2 hours)
            self.scheduler.add_job(
                func=self.collect_analytics,
                trigger=CronTrigger(hour='*/2', timezone=timezone),
                id='collect_analytics',
                name='Collect Analytics',
                max_instances=1
            )
            
            # Monthly cleanup schedule (1st of every month at 2 AM)
            self.scheduler.add_job(
                func=self.monthly_cleanup,
                trigger=CronTrigger(day=1, hour=2, timezone=timezone),
                id='monthly_cleanup',
                name='Monthly Database Cleanup',
                max_instances=1
            )
            
            logger.info("Scheduler setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduler: {e}")
            raise
    
    def start(self):
        """Start the orchestrator."""
        try:
            self.scheduler.start()
            logger.success("Job Automation Orchestrator started successfully")
            
            # Trigger immediate job fetch and processing
            logger.info("🚀 Triggering initial job fetch and processing...")
            self.fetch_and_process_jobs()
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                self.stop()
                
        except Exception as e:
            logger.error(f"Error in orchestrator main loop: {e}")
            self.stop()
    
    def stop(self):
        """Stop the orchestrator."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
            
            # Close all poster resources
            self.social_poster_manager.close_all_posters()
            
            # Close database connections
            close_database()
            
            logger.success("Job Automation Orchestrator stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
    
    def fetch_and_process_jobs(self):
        """Fetch jobs from all sources and process them."""
        try:
            logger.info("Starting job fetch and process cycle")
            
            # Fetch jobs from all sources
            raw_jobs = self.job_fetcher_manager.fetch_all_jobs()
            total_jobs = sum(len(jobs) for jobs in raw_jobs.values())
            logger.info(f"Fetched {total_jobs} raw jobs from {len(raw_jobs)} sources")
            
            if total_jobs == 0:
                logger.warning("No jobs fetched from any source")
                return
            
            # Process jobs through the pipeline
            stored_job_ids = self.job_processor.process_job_pipeline(raw_jobs)
            logger.info(f"Job processing completed. {len(stored_job_ids)} jobs stored.")
            
            # Generate captions for new jobs
            self._generate_captions_for_jobs(stored_job_ids)
            
            # Post immediately after caption generation (for testing)
            if stored_job_ids:
                logger.info("🚀 Triggering immediate posting after caption generation...")
                self.post_pending_content()
            
        except Exception as e:
            logger.error(f"Error in fetch_and_process_jobs: {e}")
        finally:
            # Close database connection after all operations
            try:
                db = get_db()
                db.close()
                logger.info("Database connection closed after job processing")
            except:
                pass
    
    def _generate_captions_for_jobs(self, job_ids: List[str]):
        """Generate captions for newly processed jobs."""
        try:
            db = get_db()
            
            for job_id in job_ids:
                try:
                    logger.info(f"Processing job_id: {job_id}")
                    # Get job data
                    jobs_collection = db.get_collection('jobs_clean')
                    from bson import ObjectId
                    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
                    if not job:
                        logger.warning(f"Job not found for job_id: {job_id}")
                        continue
                    logger.info(f"Found job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    
                    # Convert to dict for caption generation
                    job_data = {
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location'),
                        'description': job.get('description'),
                        'apply_url': job.get('apply_url'),
                        'skills': job.get('skills') or [],
                        'remote': job.get('remote'),
                        'seniority': job.get('seniority'),
                        'employment_type': job.get('employment_type')
                    }
                    
                    # Generate captions - pass as a list since caption generator expects List[Dict]
                    captions = self.caption_generator.generate_captions([job_data])
                    logger.info(f"Generated captions for job {job.get('title', 'Unknown')}: {list(captions.keys())}")
                    
                    # Store captions as pending posts
                    platforms = self.config.get('posting', {}).get('platforms', [])
                    logger.info(f"Available platforms: {platforms}")
                    for platform in platforms:
                        if platform in captions:
                            caption = captions[platform]
                            logger.info(f"Caption for {platform}: {caption[:100]}...")
                            
                            # Validate caption
                            if self.caption_generator.validate_caption(caption, platform):
                                # Optimize caption
                                optimized_caption = self.caption_generator.optimize_caption(caption, platform)
                                
                                # Store as pending post in MongoDB
                                posts_collection = db.get_collection('posts_ready')
                                pending_post = {
                                    'job_id': job_id,
                                    'platform': platform,
                                    'caption': optimized_caption,
                                    'status': 'pending',
                                    'created_at': datetime.now(),
                                    'scheduled_for': None
                                }
                                posts_collection.insert_one(pending_post)
                                
                                logger.info(f"Generated {platform} caption for job: {job.get('title', 'Unknown')}")
                            else:
                                logger.warning(f"Invalid {platform} caption for job: {job.get('title', 'Unknown')}")
                        else:
                            logger.warning(f"Platform {platform} not found in generated captions")
                    
                except Exception as e:
                    logger.error(f"Error generating captions for job {job_id}: {e}")
                    continue
            
            logger.info(f"Caption generation completed for {len(job_ids)} jobs")
            
        except Exception as e:
            logger.error(f"Error in caption generation: {e}")
    
    def post_pending_content(self, platform: Optional[str] = None):
        """Post pending content to social media platforms."""
        try:
            logger.info(f"Starting content posting cycle for platform: {platform or 'all'}")
            
            db = get_db()
            
            # Get pending posts
            posts_collection = db.get_collection('posts_ready')
            filter_query = {'status': 'pending'}
            if platform:
                filter_query['platform'] = platform
            
            pending_posts = list(posts_collection.find(filter_query))
            logger.info(f"Found {len(pending_posts)} pending posts for platform: {platform or 'all'}")
            
            if not pending_posts:
                logger.info("No pending posts to publish")
                return
            
            # Check daily posting limits
            max_posts = self.config.get('posting', {}).get('max_posts_per_day', {}).get(platform or 'linkedin', 4)
            today_posts = self._get_today_post_count(db, platform)
            logger.info(f"Daily posting limit check: {today_posts}/{max_posts} posts today for {platform or 'all platforms'}")
            
            if today_posts >= max_posts:
                logger.info(f"Daily posting limit reached for {platform or 'all platforms'}: {today_posts}/{max_posts}")
                return
            
            # Process pending posts
            posts_to_process = pending_posts[:max_posts - today_posts]
            logger.info(f"Processing {len(posts_to_process)} posts (limit: {max_posts - today_posts})")
            for i, post in enumerate(posts_to_process):
                try:
                    logger.info(f"Processing post {i+1}/{len(posts_to_process)}: {post.get('_id', 'Unknown')}")
                    # Get job data
                    jobs_collection = db.get_collection('jobs_clean')
                    from bson import ObjectId
                    job = jobs_collection.find_one({'_id': ObjectId(post['job_id'])})
                    if not job:
                        logger.warning(f"Job not found for post {post.get('_id', 'Unknown')}")
                        continue
                    logger.info(f"Found job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    
                    job_data = {
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location'),
                        'description': job.get('description'),
                        'apply_url': job.get('apply_url'),
                        'skills': job.get('skills') or [],
                        'remote': job.get('remote'),
                        'seniority': job.get('seniority'),
                        'employment_type': job.get('employment_type')
                    }
                    
                    # Use the applybutton.gif file as the image
                    image_path = "applybutton.gif"
                    if os.path.exists(image_path):
                        logger.info(f"Using applybutton.gif for job: {job_data.get('title', 'Unknown')}")
                    else:
                        logger.warning(f"applybutton.gif not found, posting without image")
                        image_path = None
                    
                    # Post to social media with image
                    captions = {post['platform']: post['caption']}
                    results = self.social_poster_manager.post_to_all_platforms(captions, job_data, image_path)
                    
                    # Update post status
                    if results.get(post['platform'], (False, None))[0]:
                        # Update post status to posted
                        posts_collection.update_one(
                            {'_id': post['_id']}, 
                            {'$set': {'status': 'posted'}}
                        )
                        
                        # Create posted item record
                        posted_items_collection = db.get_collection('posted_items')
                        posted_item = {
                            'job_id': post['job_id'],
                            'platform': post['platform'],
                            'posted_at': datetime.utcnow(),
                            'external_post_id': results[post['platform']][1]
                        }
                        posted_items_collection.insert_one(posted_item)
                        
                        logger.info(f"Successfully posted to {post['platform']}: {job.get('title', 'Unknown')}")
                    else:
                        # Update post status to failed
                        posts_collection.update_one(
                            {'_id': post['_id']}, 
                            {'$set': {'status': 'failed'}}
                        )
                        logger.error(f"Failed to post to {post['platform']}: {job.get('title', 'Unknown')}")
                    
                    # Add delay between posts
                    time.sleep(random.uniform(30, 90))
                    
                except Exception as e:
                    logger.error(f"Error posting content: {e}")
                    post.status = 'failed'
                    continue
            
            logger.info(f"Content posting cycle completed")
            
        except Exception as e:
            logger.error(f"Error in content posting: {e}")
        finally:
            db.close()
    
    def _get_today_post_count(self, db, platform: Optional[str] = None) -> int:
        """Get the number of posts made today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        posted_items_collection = db.get_collection('posted_items')
        filter_query = {
            'posted_at': {'$gte': today_start}
        }
        
        if platform:
            filter_query['platform'] = platform
        
        return posted_items_collection.count_documents(filter_query)
    
    def collect_analytics(self):
        """Collect engagement analytics for posted content."""
        try:
            logger.info("Starting analytics collection cycle")
            
            db = get_db()
            
            # Get posted items that don't have recent analytics
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            posted_items_collection = db.get_collection('posted_items')
            analytics_collection = db.get_collection('analytics')
            
            # Find posted items without analytics or with old analytics
            posted_items = list(posted_items_collection.find({}))
            
            if not posted_items:
                logger.info("No analytics to collect")
                return
            
            for posted_item in posted_items:
                try:
                    # Collect analytics based on platform
                    if posted_item.platform == 'linkedin':
                        # LinkedIn analytics collection would require additional implementation
                        metrics = {}
                    else:
                        continue
                    
                    # Store analytics
                    analytics_data = {
                        'post_id': posted_item['_id'],
                        'collected_at': datetime.utcnow(),
                        'impressions': metrics.get('impressions'),
                        'likes': metrics.get('likes'),
                        'comments': metrics.get('comments'),
                        'shares': metrics.get('shares'),
                        'clicks': metrics.get('clicks')
                    }
                    analytics_collection.insert_one(analytics_data)
                    
                    logger.info(f"Collected analytics for {posted_item['platform']} post: {posted_item['_id']}")
                    
                except Exception as e:
                    logger.error(f"Error collecting analytics for post {posted_item['_id']}: {e}")
                    continue
            
            logger.info(f"Analytics collection completed for {len(posted_items)} posts")
            
        except Exception as e:
            logger.error(f"Error in analytics collection: {e}")
        finally:
            db.close()
    
    def monthly_cleanup(self):
        """Perform monthly database cleanup."""
        try:
            logger.info("🔄 Starting monthly database cleanup...")
            
            db = get_db()
            collections = ['raw_jobs', 'clean_jobs', 'posts_ready', 'posted_items']
            total_deleted = 0
            
            for collection_name in collections:
                try:
                    collection = db.get_collection(collection_name)
                    count_before = collection.count_documents({})
                    result = collection.delete_many({})
                    total_deleted += result.deleted_count
                    logger.info(f"Cleared {collection_name}: {count_before} documents deleted")
                except Exception as e:
                    logger.error(f"Error clearing {collection_name}: {e}")
                    continue
            
            # Log cleanup activity
            cleanup_collection = db.get_collection('cleanup_logs')
            cleanup_log = {
                'timestamp': datetime.utcnow(),
                'action': 'monthly_cleanup',
                'documents_deleted': total_deleted,
                'collections_cleared': collections
            }
            cleanup_collection.insert_one(cleanup_log)
            
            logger.success(f"✅ Monthly cleanup completed! Total documents deleted: {total_deleted}")
            
        except Exception as e:
            logger.error(f"❌ Error in monthly cleanup: {e}")
        finally:
            db.close()
    
    def run_manual_job_fetch(self):
        """Manually trigger job fetching and processing."""
        logger.info("Manual job fetch triggered")
        self.fetch_and_process_jobs()
    
    def run_manual_posting(self, platform: Optional[str] = None):
        """Manually trigger content posting."""
        logger.info(f"Manual posting triggered for platform: {platform or 'all'}")
        self.post_pending_content(platform)
    
    def run_manual_caption_generation(self):
        """Manually trigger caption generation for existing clean jobs."""
        try:
            logger.info("Manual caption generation triggered")
            db = get_db()
            
            # Get all clean jobs that don't have pending posts
            jobs_collection = db.get_collection('jobs_clean')
            posts_collection = db.get_collection('posts_ready')
            
            # Get job IDs that already have pending posts
            existing_post_job_ids = set()
            existing_posts = posts_collection.find({'status': 'pending'})
            for post in existing_posts:
                existing_post_job_ids.add(post['job_id'])
            
            # Get clean jobs that don't have pending posts
            clean_jobs = jobs_collection.find({})
            job_ids_to_process = []
            
            for job in clean_jobs:
                job_id = str(job['_id'])
                if job_id not in existing_post_job_ids:
                    job_ids_to_process.append(job_id)
            
            if job_ids_to_process:
                logger.info(f"Generating captions for {len(job_ids_to_process)} existing clean jobs")
                self._generate_captions_for_jobs(job_ids_to_process)
            else:
                logger.info("All clean jobs already have pending posts")
                
        except Exception as e:
            logger.error(f"Error in manual caption generation: {e}")
        finally:
            db.close()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            db = get_db()
            
            # Get MongoDB collections
            raw_jobs_collection = db.get_collection('jobs_raw')
            clean_jobs_collection = db.get_collection('jobs_clean')
            posts_ready_collection = db.get_collection('posts_ready')
            posted_items_collection = db.get_collection('posted_items')
            analytics_collection = db.get_collection('analytics')
            
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'scheduler_running': self.scheduler.running,
                'database_connected': True,
                'job_counts': {
                    'raw_jobs': raw_jobs_collection.count_documents({}),
                    'clean_jobs': clean_jobs_collection.count_documents({}),
                    'pending_posts': posts_ready_collection.count_documents({'status': 'pending'}),
                    'posted_items': posted_items_collection.count_documents({}),
                    'analytics_records': analytics_collection.count_documents({})
                },
                'components': {
                    'job_fetchers': len(self.job_fetcher_manager.fetchers),
                    'social_posters': len(self.social_poster_manager.posters),
                    'caption_generator': self.caption_generator is not None
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
        finally:
            db.close()

def main():
    """Main entry point."""
    try:
        # Setup logging
        logger.add(
            "logs/job_automation.log",
            rotation="10 MB",
            retention="30 days",
            level="INFO"
        )
        
        # Create and start orchestrator
        orchestrator = JobAutomationOrchestrator()
        orchestrator.start()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()
