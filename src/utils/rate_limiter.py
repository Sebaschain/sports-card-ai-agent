"""
Rate Limiter para APIs externas
Implementa rate limiting con token bucket algorithm
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Any


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_minute / 60
        self.tokens = defaultdict(lambda: requests_per_minute)
        self.last_update = defaultdict(time.time)
        self.lock = Lock()

    def acquire(self, key: str = "default") -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update[key]
            self.tokens[key] = min(
                self.requests_per_minute, self.tokens[key] + elapsed * self.requests_per_second
            )
            self.last_update[key] = now

            if self.tokens[key] >= 1:
                self.tokens[key] -= 1
                return True
            return False

    def wait_if_needed(self, key: str = "default"):
        while not self.acquire(key):
            time.sleep(0.1)

    def get_remaining(self, key: str = "default") -> int:
        with self.lock:
            return int(self.tokens.get(key, self.requests_per_minute))


class APIRateLimiter:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, requests_per_minute: int = 30):
        if not hasattr(self, "initialized"):
            self.limiter = RateLimiter(requests_per_minute)
            self.ebay_limiter = RateLimiter(requests_per_minute * 10)
            self.initialized = True

    def check_limit(self, api: str = "default") -> bool:
        if api == "ebay":
            return self.ebay_limiter.acquire("ebay")
        return self.limiter.acquire(api)

    def wait_if_needed(self, api: str = "default"):
        if api == "ebay":
            self.ebay_limiter.wait_if_needed("ebay")
        else:
            self.limiter.wait_if_needed(api)

    def get_remaining(self, api: str = "default") -> int:
        if api == "ebay":
            return self.ebay_limiter.get_remaining("ebay")
        return self.limiter.get_remaining(api)


rate_limiter = APIRateLimiter(requests_per_minute=30)


def rate_limit(api: str = "default"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed(api)
            return func(*args, **kwargs)

        return wrapper

    return decorator
