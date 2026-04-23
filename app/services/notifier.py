"""
Telegram Notifier
"""

class Notifier:
    def __init__(self):
        self.bot_token = None
        self.chat_id = None
    
    def notify_success(self, post):
        """Send success notification"""
        print(f"✅ Post {post.id} published successfully")
    
    def notify_failure(self, post, error):
        """Send failure notification"""
        print(f"❌ Post {post.id} failed: {error}")


notifier = Notifier()
