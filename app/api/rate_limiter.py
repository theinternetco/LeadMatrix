import time
from fastapi import HTTPException, status

class RateLimiter:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.timestamps = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - 60
        if key not in self.timestamps:
            self.timestamps[key] = []
        self.timestamps[key] = [ts for ts in self.timestamps[key] if ts > window_start]
        if len(self.timestamps[key]) >= self.calls_per_minute:
            return False
        self.timestamps[key].append(now)
        return True

rate_limiter = RateLimiter(calls_per_minute=60)

def check_rate_limit(api_key: str):
    if not rate_limiter.is_allowed(api_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
