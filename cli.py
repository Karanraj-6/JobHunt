"""
Command-line interface for the job automation application.
"""
import argparse
import sys
import os
from datetime import datetime
from loguru import logger
import yaml

from orchestrator import JobAutomationOrchestrator
from database import init_database, get_db
from models import JobsClean, PostsReady, PostedItems, Analytics

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
        db_manager = init_database(args.config)
        db_manager.create_tables()
        logger.success("Database initialized successfully")
        
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

def list_jobs_command(args):
    """List jobs in the system."""
    try:
        init_database(args.config)
        db = get_db()
        
        query = db.query(JobsClean)
        
        # Apply filters
        if args.company:
            query = query.filter(JobsClean.company.ilike(f"%{args.company}%"))
        
        if args.location:
            query = query.filter(JobsClean.location.ilike(f"%{args.location}%"))
        
        if args.skills:
            skills_filter = args.skills.split(',')
            for skill in skills_filter:
                query = query.filter(JobsClean.skills.contains([skill.strip()]))
        
        # Apply limit
        if args.limit:
            query = query.limit(args.limit)
        
        jobs = query.all()
        
        print(f"\n=== Jobs ({len(jobs)} found) ===")
        for job in jobs:
            print(f"\nTitle: {job.title}")
            print(f"Company: {job.company}")
            print(f"Location: {job.location}")
            print(f"Skills: {', '.join(job.skills) if job.skills else 'None'}")
            print(f"Remote: {'Yes' if job.remote else 'No'}")
            print(f"Created: {job.created_at}")
            print(f"Apply URL: {job.apply_url}")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        sys.exit(1)
    finally:
        db.close()

def list_posts_command(args):
    """List posts in the system."""
    try:
        init_database(args.config)
        db = get_db()
        
        query = db.query(PostsReady)
        
        # Apply filters
        if args.platform:
            query = query.filter(PostsReady.platform == args.platform)
        
        if args.status:
            query = query.filter(PostsReady.status == args.status)
        
        # Apply limit
        if args.limit:
            query = query.limit(args.limit)
        
        posts = query.all()
        
        print(f"\n=== Posts ({len(posts)} found) ===")
        for post in posts:
            print(f"\nPlatform: {post.platform}")
            print(f"Status: {post.status}")
            print(f"Created: {post.created_at}")
            print(f"Scheduled: {post.scheduled_for or 'Not scheduled'}")
            print(f"Caption Preview: {post.caption[:100]}...")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to list posts: {e}")
        sys.exit(1)
    finally:
        db.close()

def analytics_command(args):
    """Show analytics data."""
    try:
        init_database(args.config)
        db = get_db()
        
        query = db.query(Analytics).join(PostedItems)
        
        # Apply filters
        if args.platform:
            query = query.filter(PostedItems.platform == args.platform)
        
        # Apply limit
        if args.limit:
            query = query.limit(args.limit)
        
        analytics = query.all()
        
        print(f"\n=== Analytics ({len(analytics)} records) ===")
        for record in analytics:
            print(f"\nPost ID: {record.post_id}")
            print(f"Collected: {record.collected_at}")
            print(f"Impressions: {record.impressions or 'N/A'}")
            print(f"Likes: {record.likes or 'N/A'}")
            print(f"Comments: {record.comments or 'N/A'}")
            print(f"Shares: {record.shares or 'N/A'}")
            print(f"Clicks: {record.clicks or 'N/A'}")
            print("-" * 50)
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        sys.exit(1)
    finally:
        db.close()

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
  python cli.py analytics --platform x  # Show X analytics
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
        choices=['linkedin', 'x'],
        help='Platform to post to (default: all)'
    )
    
    # List jobs command
    list_jobs_parser = subparsers.add_parser('list-jobs', help='List jobs')
    list_jobs_parser.add_argument('--company', help='Filter by company name')
    list_jobs_parser.add_argument('--location', help='Filter by location')
    list_jobs_parser.add_argument('--skills', help='Filter by skills (comma-separated)')
    list_jobs_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # List posts command
    list_posts_parser = subparsers.add_parser('list-posts', help='List posts')
    list_posts_parser.add_argument('--platform', choices=['linkedin', 'x'], help='Filter by platform')
    list_posts_parser.add_argument('--status', choices=['pending', 'posted', 'failed'], help='Filter by status')
    list_posts_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Show analytics')
    analytics_parser.add_argument('--platform', choices=['linkedin', 'x'], help='Filter by platform')
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

