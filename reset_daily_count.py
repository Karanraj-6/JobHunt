from database import DatabaseManager
from config import config
from datetime import datetime, timedelta

# Initialize database
db = DatabaseManager(config)

# Get collections
ready_collection = db.get_collection('posts_ready')
posted_collection = db.get_collection('posted_items')

# Get today's and yesterday's dates
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
yesterday = today - timedelta(days=1)

print(f"Today: {today}")
print(f"Yesterday: {yesterday}")

# Count posts before reset
ready_count_before = ready_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})
posted_count_before = posted_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})

print(f"\nBefore reset:")
print(f"Posts ready today: {ready_count_before}")
print(f"Posted items today: {posted_count_before}")

# Reset daily count by moving today's posts to yesterday
if ready_count_before > 0:
    result = ready_collection.update_many(
        {'platform': 'linkedin', 'created_at': {'$gte': today}},
        {'$set': {'created_at': yesterday}}
    )
    print(f"\nUpdated {result.modified_count} posts_ready records to yesterday")

if posted_count_before > 0:
    result = posted_collection.update_many(
        {'platform': 'linkedin', 'created_at': {'$gte': today}},
        {'$set': {'created_at': yesterday}}
    )
    print(f"Updated {result.modified_count} posted_items records to yesterday")

# Count posts after reset
ready_count_after = ready_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})
posted_count_after = posted_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})

print(f"\nAfter reset:")
print(f"Posts ready today: {ready_count_after}")
print(f"Posted items today: {posted_count_after}")

db.close()
