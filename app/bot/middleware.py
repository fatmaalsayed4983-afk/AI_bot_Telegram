import time
from app.database.db_manager import DBManager

class BotMiddleware:
    def __init__(self, db: DBManager):
        self.db = db
        self.rate_limits = {}  # {user_id: [timestamps]}

    def is_rate_limited(self, user_id: int, limit: int = 15, period: int = 60) -> bool:
        # Allow 15 messages per 60 seconds by default
        now = time.time()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
            
        # Filter timestamps within current timeframe window
        self.rate_limits[user_id] = [t for t in self.rate_limits[user_id] if now - t < period]
        
        if len(self.rate_limits[user_id]) >= limit:
            return True
            
        self.rate_limits[user_id].append(now)
        return False

    def process_user(self, telegram_id: int, username: str) -> dict:
        user = self.db.get_or_create_user(telegram_id, username)
        return user
