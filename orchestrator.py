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

from database import init_database, get_db, close_database
from job_fetchers import JobFetcherManager
from job_processor import JobProcessor
from caption_generator import CaptionGenerator
from image_generator import ImageGenerationManager
from social_posters import SocialPosterManager
from models import JobsClean, PostsReady, PostedItems, Analytics

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
            
            logger.info("Scheduler setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduler: {e}")
            raise
    
    def start(self):
        """Start the orchestrator."""
        try:
            self.scheduler.start()
            logger.success("Job Automation Orchestrator started successfully")
            
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
            
        except Exception as e:
            logger.error(f"Error in fetch_and_process_jobs: {e}")
    
    def _generate_captions_for_jobs(self, job_ids: List[str]):
        """Generate captions for newly processed jobs."""
        try:
            db = get_db()
            
            for job_id in job_ids:
                try:
                    # Get job data
                    job = db.query(JobsClean).filter(JobsClean.id == job_id).first()
                    if not job:
                        continue
                    
                    # Convert to dict for caption generation
                    job_data = {
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'description': job.description,
                        'apply_url': job.apply_url,
                        'skills': job.skills or [],
                        'remote': job.remote,
                        'seniority': job.seniority,
                        'employment_type': job.employment_type
                    }
                    
                    # Generate captions
                    captions = self.caption_generator.generate_captions(job_data)
                    
                    # Store captions as pending posts
                    platforms = self.config.get('posting', {}).get('platforms', [])
                    for platform in platforms:
                        if platform in captions:
                            caption = captions[platform]
                            
                            # Validate caption
                            if self.caption_generator.validate_caption(caption, platform):
                                # Optimize caption
                                optimized_caption = self.caption_generator.optimize_caption(caption, platform)
                                
                                # Store as pending post
                                pending_post = PostsReady(
                                    job_id=job_id,
                                    platform=platform,
                                    caption=optimized_caption,
                                    status='pending'
                                )
                                db.add(pending_post)
                                
                                logger.info(f"Generated {platform} caption for job: {job.title}")
                            else:
                                logger.warning(f"Invalid {platform} caption for job: {job.title}")
                    
                except Exception as e:
                    logger.error(f"Error generating captions for job {job_id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Caption generation completed for {len(job_ids)} jobs")
            
        except Exception as e:
            logger.error(f"Error in caption generation: {e}")
            db.rollback()
        finally:
            db.close()
    
    def post_pending_content(self, platform: Optional[str] = None):
        """Post pending content to social media platforms."""
        try:
            logger.info(f"Starting content posting cycle for platform: {platform or 'all'}")
            
            db = get_db()
            
            # Get pending posts
            query = db.query(PostsReady).filter(PostsReady.status == 'pending')
            if platform:
                query = query.filter(PostsReady.platform == platform)
            
            pending_posts = query.all()
            
            if not pending_posts:
                logger.info("No pending posts to publish")
                return
            
            # Check daily posting limits
            max_posts = self.config.get('posting', {}).get('max_posts_per_day', {}).get(platform or 'linkedin', 4)
            today_posts = self._get_today_post_count(db, platform)
            
            if today_posts >= max_posts:
                logger.info(f"Daily posting limit reached for {platform or 'all platforms'}: {today_posts}/{max_posts}")
                return
            
            # Process pending posts
            for post in pending_posts[:max_posts - today_posts]:
                try:
                    # Get job data
                    job = db.query(JobsClean).filter(JobsClean.id == post.job_id).first()
                    if not job:
                        continue
                    
                    job_data = {
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'description': job.description,
                        'apply_url': job.apply_url,
                        'skills': job.skills or [],
                        'remote': job.remote,
                        'seniority': job.seniority,
                        'employment_type': job.employment_type
                    }
                    
                    # Generate image for the job if enabled
                    image_path = None
                    if self.config.get('image_generation', {}).get('enabled', False):
                        try:
                            image_path = self.image_generation_manager.generator.generate_job_image(job_data)
                            if image_path:
                                logger.info(f"Generated image for job: {image_path}")
                            else:
                                logger.warning("Failed to generate image for job")
                        except Exception as e:
                            logger.error(f"Error generating image: {e}")
                    
                    # Post to social media with image
                    captions = {post.platform: post.caption}
                    results = self.social_poster_manager.post_to_all_platforms(captions, job_data, image_path)
                    
                    # Update post status
                    if results.get(post.platform, (False, None))[0]:
                        post.status = 'posted'
                        
                        # Create posted item record
                        posted_item = PostedItems(
                            job_id=post.job_id,
                            platform=post.platform,
                            posted_at=datetime.utcnow(),
                            external_post_id=results[post.platform][1]
                        )
                        db.add(posted_item)
                        
                        logger.info(f"Successfully posted to {post.platform}: {job.title}")
                    else:
                        post.status = 'failed'
                        logger.error(f"Failed to post to {post.platform}: {job.title}")
                    
                    # Add delay between posts
                    time.sleep(random.uniform(30, 90))
                    
                except Exception as e:
                    logger.error(f"Error posting content: {e}")
                    post.status = 'failed'
                    continue
            
            db.commit()
            logger.info(f"Content posting cycle completed")
            
        except Exception as e:
            logger.error(f"Error in content posting: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _get_today_post_count(self, db, platform: Optional[str] = None) -> int:
        """Get the number of posts made today."""
        today = datetime.utcnow().date()
        
        query = db.query(PostedItems).filter(
            PostedItems.posted_at >= today
        )
        
        if platform:
            query = query.filter(PostedItems.platform == platform)
        
        return query.count()
    
    def collect_analytics(self):
        """Collect engagement analytics for posted content."""
        try:
            logger.info("Starting analytics collection cycle")
            
            db = get_db()
            
            # Get posted items that don't have recent analytics
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            posted_items = db.query(PostedItems).outerjoin(Analytics).filter(
                (Analytics.id.is_(None)) | (Analytics.collected_at < cutoff_time)
            ).all()
            
            if not posted_items:
                logger.info("No analytics to collect")
                return
            
            for posted_item in posted_items:
                try:
                    # Collect analytics based on platform
                    if posted_item.platform == 'x':
                        metrics = self.social_poster_manager.posters['x'].get_tweet_metrics(
                            posted_item.external_post_id
                        )
                    elif posted_item.platform == 'linkedin':
                        # LinkedIn analytics collection would require additional implementation
                        metrics = {}
                    else:
                        continue
                    
                    # Store analytics
                    analytics = Analytics(
                        post_id=posted_item.id,
                        collected_at=datetime.utcnow(),
                        impressions=metrics.get('impressions'),
                        likes=metrics.get('likes'),
                        comments=metrics.get('comments'),
                        shares=metrics.get('shares'),
                        clicks=metrics.get('clicks')
                    )
                    db.add(analytics)
                    
                    logger.info(f"Collected analytics for {posted_item.platform} post: {posted_item.id}")
                    
                except Exception as e:
                    logger.error(f"Error collecting analytics for post {posted_item.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Analytics collection completed for {len(posted_items)} posts")
            
        except Exception as e:
            logger.error(f"Error in analytics collection: {e}")
            db.rollback()
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
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            db = get_db()
            
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'scheduler_running': self.scheduler.running,
                'database_connected': True,
                'job_counts': {
                    'raw_jobs': db.query(JobsRaw).count(),
                    'clean_jobs': db.query(JobsClean).count(),
                    'pending_posts': db.query(PostsReady).filter(PostsReady.status == 'pending').count(),
                    'posted_items': db.query(PostedItems).count(),
                    'analytics_records': db.query(Analytics).count()
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
