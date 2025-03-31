"""
Caching utility for API responses
Implements both in-memory and file-based caching with expiry
"""

import os
import json
import time
from typing import Dict, Any, Optional, Tuple
import hashlib
from app.utils.api.config import CACHE_EXPIRY

# In-memory cache
_memory_cache: Dict[str, Tuple[float, Any]] = {}

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_cache_key(api_name: str, endpoint: str, params: Dict[str, Any]) -> str:
    """
    Generate a cache key based on API name, endpoint, and parameters
    
    Args:
        api_name: Name of the API (e.g., 'alpha_vantage', 'coingecko')
        endpoint: API endpoint (e.g., 'stock/price', 'crypto/list')
        params: Request parameters
        
    Returns:
        Unique cache key string
    """
    params_str = json.dumps(params, sort_keys=True)
    key_str = f"{api_name}:{endpoint}:{params_str}"
    return hashlib.md5(key_str.encode()).hexdigest()

def get_from_cache(api_name: str, endpoint: str, params: Dict[str, Any], cache_type: str = "memory") -> Optional[Any]:
    """
    Get data from cache if available and not expired
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint
        params: Request parameters
        cache_type: Type of cache to use ('memory' or 'file')
        
    Returns:
        Cached data if available and not expired, None otherwise
    """
    key = _get_cache_key(api_name, endpoint, params)
    expiry_time = CACHE_EXPIRY.get(endpoint.split('/')[-1], 300)  # Default 5 minutes
    
    # Check memory cache first
    if cache_type == "memory" and key in _memory_cache:
        timestamp, data = _memory_cache[key]
        if time.time() - timestamp < expiry_time:
            return data
        else:
            # Remove expired data
            del _memory_cache[key]
    
    # Check file cache if requested or memory cache not available
    if cache_type == "file" or (cache_type == "memory" and key not in _memory_cache):
        cache_file = os.path.join(CACHE_DIR, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                timestamp = cache_data.get('timestamp', 0)
                if time.time() - timestamp < expiry_time:
                    return cache_data.get('data')
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    return None

def save_to_cache(api_name: str, endpoint: str, params: Dict[str, Any], data: Any, cache_type: str = "memory") -> None:
    """
    Save data to cache
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint
        params: Request parameters
        data: Data to cache
        cache_type: Type of cache to use ('memory', 'file', or 'both')
    """
    key = _get_cache_key(api_name, endpoint, params)
    
    # Save to memory cache
    if cache_type in ["memory", "both"]:
        _memory_cache[key] = (time.time(), data)
    
    # Save to file cache
    if cache_type in ["file", "both"]:
        cache_file = os.path.join(CACHE_DIR, f"{key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'data': data
                }, f)
        except (IOError, OSError) as e:
            print(f"Error saving to file cache: {str(e)}")

def clear_cache(api_name: Optional[str] = None, endpoint: Optional[str] = None, cache_type: str = "both") -> None:
    """
    Clear cache either selectively or completely
    
    Args:
        api_name: Optional API name to clear specific API cache
        endpoint: Optional endpoint to clear specific endpoint cache
        cache_type: Type of cache to clear ('memory', 'file', or 'both')
    """
    global _memory_cache
    
    # Clear memory cache
    if cache_type in ["memory", "both"]:
        if api_name is None and endpoint is None:
            _memory_cache = {}
        elif api_name is not None and endpoint is None:
            # Clear all endpoints for specific API
            _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(f"{api_name}:")}
        elif api_name is not None and endpoint is not None:
            # Clear specific API and endpoint
            prefix = f"{api_name}:{endpoint}:"
            _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(prefix)}
    
    # Clear file cache
    if cache_type in ["file", "both"]:
        if api_name is None and endpoint is None:
            # Clear all files
            for file in os.listdir(CACHE_DIR):
                if file.endswith('.json'):
                    try:
                        os.remove(os.path.join(CACHE_DIR, file))
                    except OSError:
                        pass
        else:
            # Selective file clearing for specific API/endpoint
            for file in os.listdir(CACHE_DIR):
                if file.endswith('.json'):
                    if api_name is not None and file.startswith(f"{api_name}_"):
                        if endpoint is None or file.startswith(f"{api_name}_{endpoint}_"):
                            try:
                                os.remove(os.path.join(CACHE_DIR, file))
                            except OSError:
                                pass 