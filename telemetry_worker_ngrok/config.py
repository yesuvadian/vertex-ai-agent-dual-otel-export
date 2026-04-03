"""
Configuration loaded from environment variables
"""
import os


class Config:
    """Application configuration"""

    # Portal26 Backend
    PORTAL26_ENDPOINT = os.environ.get('PORTAL26_ENDPOINT')
    PORTAL26_USERNAME = os.environ.get('PORTAL26_USERNAME')
    PORTAL26_PASSWORD = os.environ.get('PORTAL26_PASSWORD')
    PORTAL26_TIMEOUT = int(os.environ.get('PORTAL26_TIMEOUT', '30'))

    # GCP
    GCP_PROJECT = os.environ.get('GCP_PROJECT')
    GCP_LOCATION = os.environ.get('GCP_LOCATION', 'us-central1')

    # Redis (optional)
    REDIS_HOST = os.environ.get('REDIS_HOST')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))

    # Deduplication
    DEDUP_CACHE_TTL = int(os.environ.get('DEDUP_CACHE_TTL', '3600'))  # 1 hour

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Cloud Run
    PORT = int(os.environ.get('PORT', '8080'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            'PORTAL26_ENDPOINT',
            'PORTAL26_USERNAME',
            'PORTAL26_PASSWORD'
        ]
        missing = []
        for var in required:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    @classmethod
    def print_config(cls):
        """Print configuration (without secrets)"""
        print("Configuration:")
        print(f"  PORTAL26_ENDPOINT: {cls.PORTAL26_ENDPOINT}")
        print(f"  PORTAL26_USERNAME: {cls.PORTAL26_USERNAME}")
        print(f"  PORTAL26_PASSWORD: {'*' * 8 if cls.PORTAL26_PASSWORD else 'NOT SET'}")
        print(f"  GCP_PROJECT: {cls.GCP_PROJECT}")
        print(f"  GCP_LOCATION: {cls.GCP_LOCATION}")
        print(f"  REDIS_HOST: {cls.REDIS_HOST or 'NOT SET (using memory cache)'}")
        print(f"  DEDUP_CACHE_TTL: {cls.DEDUP_CACHE_TTL}s")
        print(f"  LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"  PORT: {cls.PORT}")
