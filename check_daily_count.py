from database import DatabaseManager
from config import config
from datetime import datetime

# Initialize database
db = DatabaseManager(config)

# Check posted_items collection
posted_collection = db.get_collection('posted_items')
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

posted_count = posted_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})
print(f'Posted items today: {posted_count}')

# Check posts_ready collection
ready_collection = db.get_collection('posts_ready')
ready_count = ready_collection.count_documents({'platform': 'linkedin', 'created_at': {'$gte': today}})
print(f'Posts ready today: {ready_count}')

# Check all posts from today in both collections
print(f"\nPosted items from today:")
posted_posts = list(posted_collection.find({'platform': 'linkedin', 'created_at': {'$gte': today}}))
for post in posted_posts:
    print(f"- {post.get('status', 'N/A')}: {post.get('created_at', 'N/A')}")

print(f"\nPosts ready from today:")
ready_posts = list(ready_collection.find({'platform': 'linkedin', 'created_at': {'$gte': today}}))
for post in ready_posts:
    print(f"- {post.get('status', 'N/A')}: {post.get('created_at', 'N/A')}")

db.close()
