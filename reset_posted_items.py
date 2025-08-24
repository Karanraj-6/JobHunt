from database import DatabaseManager
from config import config
from datetime import datetime, timedelta

# Initialize database
db = DatabaseManager(config)

# Get posted_items collection
posted_collection = db.get_collection('posted_items')

# Get today's and yesterday's dates
today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today - timedelta(days=1)

print(f"Today: {today}")
print(f"Yesterday: {yesterday}")

# Count posted items before reset
posted_count_before = posted_collection.count_documents({'platform': 'linkedin', 'posted_at': {'$gte': today}})
print(f"\nPosted items today before reset: {posted_count_before}")

# Show posted items from today
if posted_count_before > 0:
    print("\nPosted items from today:")
    today_posts = list(posted_collection.find({'platform': 'linkedin', 'posted_at': {'$gte': today}}))
    for post in today_posts:
        print(f"- Posted at: {post.get('posted_at')}, Job ID: {post.get('job_id')}")

# Reset daily count by moving today's posted items to yesterday
if posted_count_before > 0:
    result = posted_collection.update_many(
        {'platform': 'linkedin', 'posted_at': {'$gte': today}},
        {'$set': {'posted_at': yesterday}}
    )
    print(f"\nUpdated {result.modified_count} posted items to yesterday")

# Count posted items after reset
posted_count_after = posted_collection.count_documents({'platform': 'linkedin', 'posted_at': {'$gte': today}})
print(f"Posted items today after reset: {posted_count_after}")

db.close()
