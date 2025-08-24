from database import DatabaseManager
from config import config
from datetime import datetime

# Initialize database
db = DatabaseManager(config)

# Get collections
posted_collection = db.get_collection('posted_items')
ready_collection = db.get_collection('posts_ready')

# Get today's date (start of day)
today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
print(f"Today start: {today_start}")

# Check posted_items collection
filter_query = {
    'posted_at': {'$gte': today_start}
}
filter_query['platform'] = 'linkedin'

posted_count = posted_collection.count_documents(filter_query)
print(f"Posted items count with filter: {posted_count}")

# Show the filter query
print(f"Filter query: {filter_query}")

# Check if there are any posted_items at all
all_posted = list(posted_collection.find({}))
print(f"Total posted_items: {len(all_posted)}")

if all_posted:
    print("Sample posted item:")
    sample = all_posted[0]
    print(f"- ID: {sample.get('_id')}")
    print(f"- Platform: {sample.get('platform')}")
    print(f"- Posted at: {sample.get('posted_at')}")
    print(f"- Job ID: {sample.get('job_id')}")

# Show all posted items from today
print(f"\nPosted items from today:")
today_posts = list(posted_collection.find(filter_query))
for post in today_posts:
    print(f"- Posted at: {post.get('posted_at')}, Job ID: {post.get('job_id')}")

# Check posts_ready collection
ready_count = ready_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today_start}})
print(f"\nPosts ready today: {ready_count}")

db.close()
