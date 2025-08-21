"""Base API client for external data sources"""

import time
import requests
import logging
from typing import Dict, Any, Optional, Union
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from src.utils.api_config import FINANCIAL_DATA_PROVIDERS, RETRY_CONFIG, RATE_LIMIT_CONFIG
from src.utils.logging import get_app_logger

logger = get_app_logger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class RateLimitExceeded(APIError):
    """Exception raised when API rate limit is exceeded"""
    pass

class AuthenticationError(APIError):
    """Exception raised when API authentication fails"""
    pass

class BaseAPIClient:
    """Base client for making API requests with retry logic and rate limiting"""
    
    def __init__(self, provider_name: str):
        """Initialize API client for a specific provider
        
        Args:
            provider_name: Name of the provider (must be in FINANCIAL_DATA_PROVIDERS)
        """
        if provider_name not in FINANCIAL_DATA_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available providers: {list(FINANCIAL_DATA_PROVIDERS.keys())}")
            
        self.provider_name = provider_name
        self.config = FINANCIAL_DATA_PROVIDERS[provider_name]
        self.base_url = self.config['base_url']
        self.api_key = self.config['api_key']
        self.default_params = self.config['default_params']
        
        # Rate limiting tracking
        self.rate_limits = RATE_LIMIT_CONFIG.get(provider_name, {})
        self._request_timestamps = []
        
        # Set up session with retry logic
        self.session = self._create_session()
        
        # Validate API key
        if not self.api_key:
            logger.warning(f"No API key provided for {provider_name}. API calls may fail.")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=RETRY_CONFIG['max_retries'],
            backoff_factor=RETRY_CONFIG['backoff_factor'],
            status_forcelist=RETRY_CONFIG['status_forcelist'],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _check_rate_limit(self):
        """Check if we're exceeding the rate limit and wait if necessary"""
        if not self.rate_limits:
            return
            
        # Clean up old timestamps
        current_time = time.time()
        minute_ago = current_time - 60
        day_ago = current_time - 86400  # 24 hours in seconds
        
        # Keep only timestamps from the last day
        self._request_timestamps = [ts for ts in self._request_timestamps if ts > day_ago]
        
        # Check requests per minute
        requests_last_minute = len([ts for ts in self._request_timestamps if ts > minute_ago])
        if requests_last_minute >= self.rate_limits.get('requests_per_minute', float('inf')):
            wait_time = 60 - (current_time - self._request_timestamps[-self.rate_limits['requests_per_minute']])
            logger.warning(f"Rate limit approaching for {self.provider_name}. Waiting {wait_time:.2f} seconds.")
            time.sleep(max(0, wait_time))
        
        # Check requests per day
        if len(self._request_timestamps) >= self.rate_limits.get('requests_per_day', float('inf')):
            raise RateLimitExceeded(f"Daily rate limit exceeded for {self.provider_name}")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {self.provider_name}", 
                                         status_code=response.status_code, 
                                         response=response.text)
            elif response.status_code == 429:
                raise RateLimitExceeded(f"Rate limit exceeded for {self.provider_name}", 
                                      status_code=response.status_code, 
                                      response=response.text)
            else:
                raise APIError(f"HTTP error occurred: {str(e)}", 
                              status_code=response.status_code, 
                              response=response.text)
        except ValueError:
            raise APIError(f"Invalid JSON response from {self.provider_name}", 
                          response=response.text)
    
    def request(self, 
               endpoint: str, 
               method: str = 'GET', 
               params: Optional[Dict[str, Any]] = None, 
               data: Optional[Dict[str, Any]] = None, 
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make an API request with rate limiting and error handling
        
        Args:
            endpoint: API endpoint (will be appended to base_url)
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body for POST/PUT requests
            headers: Additional headers
            
        Returns:
            API response as dictionary
        """
        # Check rate limits
        self._check_rate_limit()
        
        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        
        # Combine default params with provided params
        request_params = self.default_params.copy()
        if params:
            request_params.update(params)
            
        # Add API key if available
        if self.api_key:
            # Different APIs use different parameter names for API keys
            if self.provider_name == 'alpha_vantage':
                request_params['apikey'] = self.api_key
            elif self.provider_name == 'financial_modeling_prep':
                request_params['apikey'] = self.api_key
            elif self.provider_name == 'marketstack':
                request_params['access_key'] = self.api_key
            elif self.provider_name == 'news_api':
                request_params['apiKey'] = self.api_key
            else:
                # Default to 'api_key' parameter
                request_params['api_key'] = self.api_key
        
        # Make request and track timestamp
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=request_params,
                json=data,
                headers=headers
            )
            
            # Record timestamp for rate limiting
            self._request_timestamps.append(time.time())
            
            # Process response
            return self._handle_response(response)
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.error(f"Connection error for {self.provider_name}: {str(e)}")
            raise APIError(f"Connection error: {str(e)}")