"""Configuration for external API connections"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Financial data API configurations
FINANCIAL_DATA_PROVIDERS = {
    "alpha_vantage": {
        "base_url": "https://www.alphavantage.co/query",
        "api_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "default_params": {
            "datatype": "json",
            "outputsize": "compact"
        }
    },
    "financial_modeling_prep": {
        "base_url": "https://financialmodelingprep.com/api/v3",
        "api_key": os.getenv("FMP_API_KEY"),
        "default_params": {}
    },
    "marketstack": {
        "base_url": "http://api.marketstack.com/v1",
        "api_key": os.getenv("MARKETSTACK_API_KEY"),
        "default_params": {
            "limit": 100
        }
    },
    "news_api": {
        "base_url": "https://newsapi.org/v2",
        "api_key": os.getenv("NEWS_API_KEY"),
        "default_params": {
            "language": "en",
            "sortBy": "publishedAt"
        }
    }
}

# Database configurations
DATABASE_CONFIGS = {
    "postgres": {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "credtech"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "connection_string": lambda: f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'credtech')}"
    }
}

# API rate limiting settings
RATE_LIMIT_CONFIG = {
    "alpha_vantage": {
        "requests_per_minute": 5,
        "requests_per_day": 500
    },
    "financial_modeling_prep": {
        "requests_per_minute": 10,
        "requests_per_day": 250
    },
    "marketstack": {
        "requests_per_minute": 5,
        "requests_per_day": 1000
    },
    "news_api": {
        "requests_per_minute": 10,
        "requests_per_day": 100
    }
}

# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504]
}