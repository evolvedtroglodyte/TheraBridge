import time
import asyncio
from threading import Lock
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Token bucket rate limiter for controlling request frequency.
    Thread-safe implementation with both sync and async support.
    """

    def __init__(self, requests_per_second: float = None):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Rate limit (default from settings)
        """
        self.rate = requests_per_second or settings.requests_per_second
        self.tokens = self.rate
        self.last_update = time.time()
        self.lock = Lock()

        logger.info(
            f"RateLimiter initialized: {self.rate} req/sec "
            f"({1/self.rate:.1f}s delay between requests)"
        )

    def wait(self):
        """
        Synchronous wait - blocks until a token is available.
        Use for synchronous code.
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.tokens = 0
                self.last_update = time.time()
            else:
                self.tokens -= 1

    async def async_wait(self):
        """
        Asynchronous wait - yields control until a token is available.
        Use for async code (preferred for web scraping).
        """
        # Use threading lock for token calculation
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
            else:
                sleep_time = 0
                self.tokens -= 1

        # Sleep outside lock (async)
        if sleep_time > 0:
            logger.debug(f"Rate limit: async sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
            with self.lock:
                self.last_update = time.time()

    def reset(self):
        """Reset rate limiter to initial state."""
        with self.lock:
            self.tokens = self.rate
            self.last_update = time.time()
            logger.info("RateLimiter reset")

    @property
    def delay_seconds(self) -> float:
        """Calculate delay between requests in seconds."""
        return 1 / self.rate

    def __repr__(self):
        return (
            f"RateLimiter(rate={self.rate} req/sec, "
            f"delay={self.delay_seconds:.1f}s, "
            f"tokens={self.tokens:.2f})"
        )

class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts rate based on response codes.
    Slows down on 429 (rate limit) responses, speeds up on success.
    """

    def __init__(self, initial_rate: float = None, min_rate: float = 0.1, max_rate: float = 5.0):
        super().__init__(initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.initial_rate = self.rate

    def on_success(self):
        """Gradually increase rate on successful requests."""
        with self.lock:
            old_rate = self.rate
            self.rate = min(self.max_rate, self.rate * 1.1)
            if self.rate != old_rate:
                logger.info(f"Rate increased: {old_rate:.2f} -> {self.rate:.2f} req/sec")

    def on_rate_limit(self):
        """Drastically reduce rate on 429 responses."""
        with self.lock:
            old_rate = self.rate
            self.rate = max(self.min_rate, self.rate * 0.5)
            logger.warning(f"Rate limit hit! Reduced: {old_rate:.2f} -> {self.rate:.2f} req/sec")

    def on_error(self):
        """Moderately reduce rate on other errors."""
        with self.lock:
            old_rate = self.rate
            self.rate = max(self.min_rate, self.rate * 0.8)
            if self.rate != old_rate:
                logger.warning(f"Error encountered. Reduced: {old_rate:.2f} -> {self.rate:.2f} req/sec")

# Global rate limiter instance
rate_limiter = RateLimiter()
