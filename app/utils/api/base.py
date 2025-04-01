"""
Base API client with common functionality for all API integrations
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Union, List
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError

from app.utils.api.config import DEFAULT_TIMEOUT, MAX_RETRIES
from app.utils.api.cache import get_from_cache, save_to_cache

logger = logging.getLogger(__name__)

class BaseAPIClient:
    """
    Base API client with common functionality:
    - Request handling with retries
    - Response caching
    - Error handling
    - Rate limiting management
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, api_name: str = "base"):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the API
            api_key: Optional API key
            api_name: Name identifier for the API (used for caching)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.api_name = api_name
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepare request headers
        
        Args:
            additional_headers: Optional additional headers to include
            
        Returns:
            Complete headers dictionary
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "Finance-Chatbot/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            # Some APIs use different authentication methods
            headers["X-API-Key"] = self.api_key
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def _handle_rate_limits(self, response: requests.Response) -> None:
        """
        Handle rate limit information from API responses
        
        Args:
            response: API response object
        """
        # Extract rate limit headers if available
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
        if 'X-RateLimit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
            
        # If we're near the rate limit, add delay
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 5:
            delay = 1.0  # Default delay
            if self.rate_limit_reset:
                delay = max(1.0, self.rate_limit_reset - time.time())
            logger.warning(f"Rate limit almost reached for {self.api_name}. Waiting {delay:.2f} seconds")
            time.sleep(delay)
    
    def _process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Process API response with improved error handling
        
        Args:
            response: API response object
            
        Returns:
            Parsed response data
            
        Raises:
            ValueError: If response is invalid or contains an error
        """
        try:
            # Handle rate limits
            self._handle_rate_limits(response)
            
            # Check for success status code
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Handle API-specific error formats
            if isinstance(data, dict):
                # Many APIs include error information in the response even with 200 status
                if 'error' in data or 'errors' in data:
                    error_msg = data.get('error', data.get('errors', 'Unknown API error'))
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get('message', str(error_msg))
                    logger.error(f"API error from {self.api_name}: {error_msg}")
                    raise ValueError(f"API error: {error_msg}")
                    
            return data
            
        except ValueError as e:
            # JSON parsing error
            logger.error(f"Failed to parse JSON from {self.api_name}: {str(e)}")
            raise ValueError(f"Invalid response format from {self.api_name}")
            
        except requests.HTTPError as e:
            # Handle HTTP errors
            status_code = response.status_code
            error_msg = f"HTTP {status_code}"
            
            try:
                # Try to extract error details from response
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_detail = error_data.get('error', error_data.get('message', ''))
                    if error_detail:
                        error_msg = f"{error_msg}: {error_detail}"
            except ValueError:
                # If JSON parsing fails, use response text
                if response.text:
                    error_msg = f"{error_msg}: {response.text[:100]}"
            
            logger.error(f"HTTP error from {self.api_name}: {error_msg}")
            raise ValueError(f"API request failed: {error_msg}")
    
    def request(self, 
               method: str, 
               endpoint: str, 
               params: Optional[Dict[str, Any]] = None,
               data: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None,
               use_cache: bool = True,
               cache_type: str = "memory",
               timeout: Optional[float] = None) -> Any:
        """
        Make an API request with improved error handling and request management
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Optional query parameters
            data: Optional request body for POST/PUT
            headers: Optional additional headers
            use_cache: Whether to use caching
            cache_type: Type of cache to use ('memory' or 'file')
            timeout: Optional request timeout in seconds
            
        Returns:
            Parsed response data
            
        Raises:
            ValueError: If the request fails or response is invalid
        """
        method = method.upper()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = params or {}
        cache_key = endpoint
        
        # Try to get from cache first if it's a GET request
        if use_cache and method == "GET":
            cached_data = get_from_cache(self.api_name, cache_key, params, cache_type)
            if cached_data:
                logger.debug(f"Using cached data for {self.api_name}/{endpoint}")
                return cached_data
        
        # Prepare headers
        request_headers = self._prepare_headers(headers)
        
        # Execute request with retries
        retry_count = 0
        last_error = None
        
        while retry_count <= MAX_RETRIES:
            try:
                # Add delay between requests to avoid rate limiting
                current_time = time.time()
                elapsed = current_time - self.last_request_time
                if elapsed < 1.0:  # Minimum 1 second between requests
                    time.sleep(1.0 - elapsed)
                
                # Make request with timeout
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if data else None,
                    headers=request_headers,
                    timeout=timeout or DEFAULT_TIMEOUT
                )
                
                # Update last request time
                self.last_request_time = time.time()
                
                # Process response
                data = self._process_response(response)
                
                # Cache successful responses for GET requests
                if use_cache and method == "GET":
                    save_to_cache(self.api_name, cache_key, params, data, cache_type)
                
                return data
                
            except Timeout:
                last_error = "Request timed out"
                retry_count += 1
                if retry_count <= MAX_RETRIES:
                    logger.warning(f"Request timeout for {self.api_name}/{endpoint}, retrying...")
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    
            except ConnectionError:
                last_error = "Connection error"
                retry_count += 1
                if retry_count <= MAX_RETRIES:
                    logger.warning(f"Connection error for {self.api_name}/{endpoint}, retrying...")
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    
            except RequestException as e:
                last_error = str(e)
                retry_count += 1
                if retry_count <= MAX_RETRIES:
                    logger.warning(f"Request failed for {self.api_name}/{endpoint}, retrying...")
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    
            except ValueError as e:
                # Don't retry on value errors (invalid response format)
                logger.error(f"Invalid response from {self.api_name}/{endpoint}: {str(e)}")
                raise
                
            except Exception as e:
                # Don't retry on unexpected errors
                logger.error(f"Unexpected error from {self.api_name}/{endpoint}: {str(e)}")
                raise
        
        # All retries failed
        error_msg = f"Request failed after {MAX_RETRIES} retries"
        if last_error:
            error_msg = f"{error_msg}: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Convenience method for GET requests"""
        return self.request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Convenience method for POST requests"""
        return self.request("POST", endpoint, params=params, data=data, **kwargs)
        
    def put(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Convenience method for PUT requests"""
        return self.request("PUT", endpoint, params=params, data=data, **kwargs)
        
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Convenience method for DELETE requests"""
        return self.request("DELETE", endpoint, params=params, **kwargs) 