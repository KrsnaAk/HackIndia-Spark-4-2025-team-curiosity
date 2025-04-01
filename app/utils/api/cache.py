"""
Caching utility for API responses
Implements both in-memory and file-based caching with expiry
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple, Union
import hashlib
from pathlib import Path
from app.utils.api.config import CACHE_EXPIRY, CACHE_ENABLED, CACHE_TTL

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache with size limit
_memory_cache: Dict[str, Tuple[float, Any]] = {}
MAX_MEMORY_CACHE_SIZE = 1000  # Maximum number of items in memory cache

# Cache directory with error handling
try:
    CACHE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))) / 'data' / 'cache'
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to create cache directory: {str(e)}")
    CACHE_DIR = None

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
    try:
        # Sort parameters to ensure consistent keys
        params_str = json.dumps(params, sort_keys=True)
        key_str = f"{api_name}:{endpoint}:{params_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating cache key: {str(e)}")
        return hashlib.md5(f"{api_name}:{endpoint}".encode()).hexdigest()

def _cleanup_memory_cache() -> None:
    """Clean up memory cache if it exceeds size limit"""
    if len(_memory_cache) > MAX_MEMORY_CACHE_SIZE:
        # Remove oldest items
        sorted_items = sorted(_memory_cache.items(), key=lambda x: x[1][0])
        items_to_remove = len(_memory_cache) - MAX_MEMORY_CACHE_SIZE
        for key, _ in sorted_items[:items_to_remove]:
            del _memory_cache[key]
        logger.info(f"Cleaned up {items_to_remove} items from memory cache")

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
    if not CACHE_ENABLED:
        return None
        
    try:
        key = _get_cache_key(api_name, endpoint, params)
        expiry_time = CACHE_EXPIRY.get(endpoint.split('/')[-1], CACHE_TTL)
        
        # Check memory cache first
        if cache_type == "memory" and key in _memory_cache:
            timestamp, data = _memory_cache[key]
            if time.time() - timestamp < expiry_time:
                return data
            else:
                # Remove expired data
                del _memory_cache[key]
        
        # Check file cache if requested or memory cache not available
        if (cache_type == "file" or (cache_type == "memory" and key not in _memory_cache)) and CACHE_DIR:
            cache_file = CACHE_DIR / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    timestamp = cache_data.get('timestamp', 0)
                    if time.time() - timestamp < expiry_time:
                        return cache_data.get('data')
                    else:
                        # Remove expired file
                        cache_file.unlink()
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.warning(f"Error reading cache file: {str(e)}")
                    if cache_file.exists():
                        cache_file.unlink()
        
        return None
        
    except Exception as e:
        logger.error(f"Error accessing cache: {str(e)}")
        return None

def save_to_cache(api_name: str, endpoint: str, params: Dict[str, Any], data: Any, cache_type: str = "memory") -> None:
    """
    Save data to cache with improved error handling
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint
        params: Request parameters
        data: Data to cache
        cache_type: Type of cache to use ('memory', 'file', or 'both')
    """
    if not CACHE_ENABLED:
        return
        
    try:
        key = _get_cache_key(api_name, endpoint, params)
        timestamp = time.time()
        
        # Save to memory cache
        if cache_type in ["memory", "both"]:
            _memory_cache[key] = (timestamp, data)
            _cleanup_memory_cache()
        
        # Save to file cache
        if (cache_type in ["file", "both"]) and CACHE_DIR:
            cache_file = CACHE_DIR / f"{key}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'data': data
                    }, f)
            except (IOError, OSError) as e:
                logger.error(f"Error saving to file cache: {str(e)}")
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
                        
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")

def clear_cache(api_name: Optional[str] = None, endpoint: Optional[str] = None, cache_type: str = "both") -> None:
    """
    Clear cache with improved error handling
    
    Args:
        api_name: Optional API name to clear specific API cache
        endpoint: Optional endpoint to clear specific endpoint cache
        cache_type: Type of cache to clear ('memory', 'file', or 'both')
    """
    try:
        # Clear memory cache
        if cache_type in ["memory", "both"]:
            if api_name is None and endpoint is None:
                _memory_cache.clear()
            elif api_name is not None and endpoint is None:
                # Clear all endpoints for specific API
                _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(f"{api_name}:")}
            elif api_name is not None and endpoint is not None:
                # Clear specific API and endpoint
                prefix = f"{api_name}:{endpoint}:"
                _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(prefix)}
        
        # Clear file cache
        if (cache_type in ["file", "both"]) and CACHE_DIR:
            try:
                if api_name is None and endpoint is None:
                    # Clear all files
                    for file in CACHE_DIR.glob('*.json'):
                        try:
                            file.unlink()
                        except OSError as e:
                            logger.warning(f"Error removing cache file {file}: {str(e)}")
                else:
                    # Selective file clearing for specific API/endpoint
                    for file in CACHE_DIR.glob('*.json'):
                        if api_name is not None and file.name.startswith(f"{api_name}_"):
                            if endpoint is None or file.name.startswith(f"{api_name}_{endpoint}_"):
                                try:
                                    file.unlink()
                                except OSError as e:
                                    logger.warning(f"Error removing cache file {file}: {str(e)}")
            except Exception as e:
                logger.error(f"Error clearing file cache: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        stats = {
            "memory_cache_size": len(_memory_cache),
            "file_cache_size": 0,
            "cache_enabled": CACHE_ENABLED,
            "cache_ttl": CACHE_TTL
        }
        
        if CACHE_DIR:
            try:
                stats["file_cache_size"] = len(list(CACHE_DIR.glob('*.json')))
            except Exception as e:
                logger.error(f"Error getting file cache size: {str(e)}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "error": str(e),
            "memory_cache_size": 0,
            "file_cache_size": 0,
            "cache_enabled": CACHE_ENABLED,
            "cache_ttl": CACHE_TTL
        } 