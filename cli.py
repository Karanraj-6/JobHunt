"""
Command-line interface for the job automation application.
"""
import argparse
import sys
import os
from datetime import datetime
from loguru import logger
import yaml

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, environment variables may not be loaded")

from orchestrator import JobAutomationOrchestrator
from database import init_database, get_db

def setup_logging():
    """Setup logging configuration."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    logger.add(
        "logs/cli.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

def init_command(args):
    """Initialize the database and create tables."""
    try:
        logger.info("Initializing database...")
        init_database(args.config)
        logger.success("Database initialized successfully (MongoDB indexes ensured)")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

def status_command(args):
    """Show system status."""
    try:
        orchestrator = JobAutomationOrchestrator(args.config)
        status = orchestrator.get_system_status()
        
        print("\n=== Job Automation System Status ===")
        print(f"Timestamp: {status.get('timestamp', 'N/A')}")
        print(f"Scheduler Running: {status.get('scheduler_running', False)}")
        print(f"Database Connected: {status.get('database_connected', False)}")
        
        print("\n--- Job Counts ---")
        job_counts = status.get('job_counts', {})
        for key, value in job_counts.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\n--- Components ---")
        components = status.get('components', {})
        for key, value in components.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\n" + "="*40)
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        sys.exit(1)

def fetch_command(args):
    """Manually trigger job fetching."""
    try:
        logger.info("Starting manual job fetch...")
        orchestrator = JobAutomationOrchestrator(args.config)
        orchestrator.run_manual_job_fetch()
        logger.success("Manual job fetch completed")
        
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        sys.exit(1)

def post_command(args):
    """Manually trigger content posting."""
    try:
        logger.info(f"Starting manual posting for platform: {args.platform or 'all'}")
        orchestrator = JobAutomationOrchestrator(args.config)
        orchestrator.run_manual_posting(args.platform)
        logger.success("Manual posting completed")
        
    except Exception as e:
        logger.error(f"Failed to post content: {e}")
        sys.exit(1)

def generate_captions_command(args):
    """Manually trigger caption generation for existing clean jobs."""
    try:
        logger.info("Starting manual caption generation...")
        orchestrator = JobAutomationOrchestrator(args.config)
        orchestrator.run_manual_caption_generation()
        logger.success("Manual caption generation completed")
        
    except Exception as e:
        logger.error(f"Failed to generate captions: {e}")
        sys.exit(1)

def list_jobs_command(args):
    """List jobs in the system."""
    try:
        init_database(args.config)
        dbm = get_db()
        col = dbm.get_collection('jobs_clean')
        mongo_query = {}
        if args.company:
            mongo_query['company'] = { '$regex': args.company, '$options': 'i' }
        if args.location:
            mongo_query['location'] = { '$regex': args.location, '$options': 'i' }
        if args.skills:
            skills = [s.strip() for s in args.skills.split(',') if s.strip()]
            if skills:
                mongo_query['skills'] = { '$in': skills }
        cursor = col.find(mongo_query).limit(args.limit or 50)
        jobs = list(cursor)
        
        print(f"\n=== Jobs ({len(jobs)} found) ===")
        for job in jobs:
            print(f"\nTitle: {job.get('title', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")
            print(f"Skills: {', '.join(job.get('skills', [])) if job.get('skills') else 'None'}")
            print(f"Remote: {'Yes' if job.get('remote') else 'No'}")
            print(f"Created: {job.get('created_at', 'N/A')}")
            print(f"Apply URL: {job.get('apply_url', 'N/A')}")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        sys.exit(1)
    finally:
        pass

def list_posts_command(args):
    """List posts in the system."""
    try:
        init_database(args.config)
        dbm = get_db()
        col = dbm.get_collection('posts_ready')
        mongo_query = {}
        if args.platform:
            mongo_query['platform'] = args.platform
        if args.status:
            mongo_query['status'] = args.status
        cursor = col.find(mongo_query).sort('created_at', -1).limit(args.limit or 50)
        posts = list(cursor)
        
        print(f"\n=== Posts ({len(posts)} found) ===")
        for post in posts:
            print(f"\nPlatform: {post.get('platform', 'N/A')}")
            print(f"Status: {post.get('status', 'N/A')}")
            print(f"Created: {post.get('created_at', 'N/A')}")
            print(f"Scheduled: {post.get('scheduled_for', 'Not scheduled')}")
            print(f"Caption Preview: {post.get('caption', '')[:100] if post.get('caption') else 'No caption'}...")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to list posts: {e}")
        sys.exit(1)
    finally:
        pass

def analytics_command(args):
    """Show analytics data."""
    try:
        init_database(args.config)
        dbm = get_db()
        col = dbm.get_collection('analytics')
        mongo_query = {}
        if args.platform:
            # Need to filter by platform by joining posted_items; do basic filter by storing platform on analytics if available
            mongo_query['platform'] = args.platform
        cursor = col.find(mongo_query).sort('collected_at', -1).limit(args.limit or 50)
        analytics = list(cursor)
        
        print(f"\n=== Analytics ({len(analytics)} records) ===")
        for record in analytics:
            print(f"\nPost ID: {record.get('post_id', 'N/A')}")
            print(f"Collected: {record.get('collected_at', 'N/A')}")
            print(f"Impressions: {record.get('impressions', 'N/A')}")
            print(f"Likes: {record.get('likes', 'N/A')}")
            print(f"Comments: {record.get('comments', 'N/A')}")
            print(f"Shares: {record.get('shares', 'N/A')}")
            print(f"Clicks: {record.get('clicks', 'N/A')}")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        sys.exit(1)
    finally:
        pass

def start_command(args):
    """Start the orchestrator."""
    try:
        logger.info("Starting Job Automation Orchestrator...")
        orchestrator = JobAutomationOrchestrator(args.config)
        orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        orchestrator.stop()
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Job Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py init                    # Initialize database
  python cli.py status                  # Show system status
  python cli.py fetch                   # Manually fetch jobs
  python cli.py post                    # Manually post content
  python cli.py post --platform linkedin # Post to LinkedIn only
  python cli.py list-jobs --limit 10    # List 10 jobs
  python cli.py list-posts --status pending # List pending posts
  python cli.py analytics --platform linkedin # Show LinkedIn analytics
  python cli.py start                   # Start the orchestrator
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Manually fetch jobs')
    
    # Post command
    post_parser = subparsers.add_parser('post', help='Manually post content')
    post_parser.add_argument(
        '--platform', '-p',
        choices=['linkedin'],
        help='Platform to post to (default: all)'
    )
    
    # Generate captions command
    generate_captions_parser = subparsers.add_parser('generate-captions', help='Manually generate captions for existing clean jobs')
    
    # List jobs command
    list_jobs_parser = subparsers.add_parser('list-jobs', help='List jobs')
    list_jobs_parser.add_argument('--company', help='Filter by company name')
    list_jobs_parser.add_argument('--location', help='Filter by location')
    list_jobs_parser.add_argument('--skills', help='Filter by skills (comma-separated)')
    list_jobs_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # List posts command
    list_posts_parser = subparsers.add_parser('list-posts', help='List posts')
    list_posts_parser.add_argument('--platform', choices=['linkedin'], help='Filter by platform')
    list_posts_parser.add_argument('--status', choices=['pending', 'posted', 'failed'], help='Filter by status')
    list_posts_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Show analytics')
    analytics_parser.add_argument('--platform', choices=['linkedin'], help='Filter by platform')
    analytics_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the orchestrator')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Execute command
    try:
        if args.command == 'init':
            init_command(args)
        elif args.command == 'status':
            status_command(args)
        elif args.command == 'fetch':
            fetch_command(args)
        elif args.command == 'post':
            post_command(args)
        elif args.command == 'generate-captions':
            generate_captions_command(args)
        elif args.command == 'list-jobs':
            list_jobs_command(args)
        elif args.command == 'list-posts':
            list_posts_command(args)
        elif args.command == 'analytics':
            analytics_command(args)
        elif args.command == 'start':
            start_command(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

