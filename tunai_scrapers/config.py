"""Configuration management for Tunai Parser scrapers."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Centralized configuration for Tunai Parser scrapers."""

    # Singleton instance
    _instance: Optional["Config"] = None
    _loaded: bool = False

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration (only runs once due to singleton)."""
        if not self._loaded:
            self._load_environment()
            self._loaded = True

    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        # Try multiple locations for .env file
        locations = [
            Path.cwd() / ".env",  # Current working directory
            Path.home() / ".tunai_scrapers" / ".env",  # User home directory
            Path("/etc/tunai_scrapers/.env"),  # System-wide config
        ]

        # Also check TUNAI_PARSER_ENV_FILE environment variable
        if env_file := os.getenv("TUNAI_PARSER_ENV_FILE"):
            locations.insert(0, Path(env_file))

        # Load from first .env file found
        for location in locations:
            if location.exists():
                load_dotenv(location)
                self.env_file = location
                break
        else:
            # No .env file found, will use system environment variables only
            self.env_file = None

    @property
    def reddit_client_id(self) -> str | None:
        """Reddit API client ID."""
        return os.getenv("REDDIT_CLIENT_ID")

    @property
    def reddit_client_secret(self) -> str | None:
        """Reddit API client secret."""
        return os.getenv("REDDIT_CLIENT_SECRET")

    @property
    def youtube_api_key(self) -> str | None:
        """YouTube API key."""
        return os.getenv("YOUTUBE_API_KEY")

    @property
    def facebook_access_token(self) -> str | None:
        """Facebook access token."""
        return os.getenv("FACEBOOK_ACCESS_TOKEN")

    @property
    def google_cse_id(self) -> str | None:
        """Google Custom Search Engine ID."""
        return os.getenv("GOOGLE_CSE_ID")

    @property
    def google_api_key(self) -> str | None:
        """Google API key."""
        return os.getenv("GOOGLE_API_KEY")

    @property
    def twitter_bearer_token(self) -> str | None:
        """Twitter/X API bearer token."""
        return os.getenv("TWITTER_BEARER_TOKEN")

    @property
    def output_dir(self) -> Path:
        """Default output directory for scraped data."""
        return Path(os.getenv("TUNAI_PARSER_OUTPUT_DIR", "data/raw"))

    @property
    def cache_dir(self) -> Path:
        """Cache directory for temporary data."""
        return Path(os.getenv("TUNAI_PARSER_CACHE_DIR", Path.home() / ".cache" / "tunai_scrapers"))

    def get(self, key: str, default: str | None = None) -> str | None:
        """
        Get an environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        """
        Get a required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if value is None:
            raise ValueError(
                f"Required environment variable {key} is not set. "
                f"Please set it in your environment or .env file."
            )
        return value


# Global config instance
config = Config()
