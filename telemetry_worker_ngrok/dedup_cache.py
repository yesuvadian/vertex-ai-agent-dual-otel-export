"""
Deduplication cache to prevent processing the same trace multiple times
Uses Redis for distributed caching or in-memory for single instance
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class DedupCache:
    """
    Cache for deduplication of trace processing
    """

    def __init__(self):
        """
        Initialize cache - tries Redis first, falls back to in-memory
        """
        self.redis_client = None
        self.memory_cache = {}
        self.ttl_seconds = int(os.environ.get('DEDUP_CACHE_TTL', '3600'))  # 1 hour default

        # Try to connect to Redis
        redis_host = os.environ.get('REDIS_HOST')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))

        if redis_host:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except ImportError:
                logger.warning("redis library not installed, using in-memory cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")
                self.redis_client = None
        else:
            logger.info("No Redis configured, using in-memory cache")

    def is_processed(self, trace_id: str) -> bool:
        """
        Check if trace has already been processed

        Args:
            trace_id: Trace ID to check

        Returns:
            True if already processed, False otherwise
        """
        cache_key = f"trace:{trace_id}"

        if self.redis_client:
            try:
                return self.redis_client.exists(cache_key) > 0
            except Exception as e:
                logger.error(f"Redis error checking trace {trace_id}: {e}")
                # Fall back to memory cache on error
                return cache_key in self.memory_cache
        else:
            return cache_key in self.memory_cache

    def mark_processed(self, trace_id: str):
        """
        Mark trace as processed

        Args:
            trace_id: Trace ID to mark
        """
        cache_key = f"trace:{trace_id}"

        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, self.ttl_seconds, "1")
                logger.debug(f"Marked trace {trace_id} as processed in Redis")
            except Exception as e:
                logger.error(f"Redis error marking trace {trace_id}: {e}")
                # Fall back to memory cache on error
                self.memory_cache[cache_key] = True
        else:
            self.memory_cache[cache_key] = True
            logger.debug(f"Marked trace {trace_id} as processed in memory")

            # Clean up memory cache if it gets too large
            if len(self.memory_cache) > 10000:
                logger.warning("Memory cache exceeded 10000 entries, clearing old entries")
                # Simple strategy: clear half
                keys_to_remove = list(self.memory_cache.keys())[:5000]
                for key in keys_to_remove:
                    del self.memory_cache[key]

    def clear(self):
        """Clear all cache entries (for testing)"""
        if self.redis_client:
            try:
                # Clear only trace: keys
                keys = self.redis_client.keys("trace:*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} entries from Redis cache")
            except Exception as e:
                logger.error(f"Error clearing Redis cache: {e}")
        else:
            self.memory_cache.clear()
            logger.info("Cleared in-memory cache")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if self.redis_client:
            try:
                key_count = len(self.redis_client.keys("trace:*"))
                return {
                    'type': 'redis',
                    'entries': key_count,
                    'ttl': self.ttl_seconds
                }
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
                return {'type': 'redis', 'error': str(e)}
        else:
            return {
                'type': 'memory',
                'entries': len(self.memory_cache),
                'ttl': self.ttl_seconds
            }
