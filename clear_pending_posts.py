from database import DatabaseManager
from config import config

# Initialize database
db = DatabaseManager(config)

# Get posts_ready collection
ready_collection = db.get_collection('posts_ready')

# Count pending posts before clearing
pending_count_before = ready_collection.count_documents({'platform': 'linkedin', 'status': 'pending'})
print(f"Pending posts before clearing: {pending_count_before}")

# Show pending posts
if pending_count_before > 0:
    print("\nPending posts to be cleared:")
    pending_posts = list(ready_collection.find({'platform': 'linkedin', 'status': 'pending'}))
    for post in pending_posts:
        print(f"- {post.get('caption_preview', 'N/A')[:100]}...")

# Clear all pending posts
if pending_count_before > 0:
    result = ready_collection.delete_many({'platform': 'linkedin', 'status': 'pending'})
    print(f"\nCleared {result.deleted_count} pending posts")

# Count pending posts after clearing
pending_count_after = ready_collection.count_documents({'platform': 'linkedin', 'status': 'pending'})
print(f"Pending posts after clearing: {pending_count_after}")

db.close()
