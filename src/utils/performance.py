"""Performance optimization utilities for CredTech XScore"""

import time
import functools
import threading
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import psutil
import gc
import weakref
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Performance optimization utilities for the application"""
    
    def __init__(self):
        self.cache = {}
        self.performance_metrics = {}
        self.optimization_config = {
            'enable_caching': True,
            'cache_ttl': 300,  # 5 minutes
            'max_cache_size': 1000,
            'enable_compression': True,
            'enable_connection_pooling': True,
            'max_connections': 20,
            'connection_timeout': 30
        }
    
    def optimize_memory(self):
        """Optimize memory usage by cleaning up unused objects"""
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Clear cache if it's too large
        if len(self.cache) > self.optimization_config['max_cache_size']:
            self._cleanup_cache()
        
        # Log memory usage
        memory_info = psutil.virtual_memory()
        logger.info(f"Memory usage: {memory_info.percent:.1f}% ({memory_info.used / 1024**3:.1f} GB)")
        
        return {
            'garbage_collected': collected,
            'memory_usage_percent': memory_info.percent,
            'memory_used_gb': memory_info.used / 1024**3
        }
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (value, timestamp) in self.cache.items()
            if current_time - timestamp > self.optimization_config['cache_ttl']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
    
    def put(self, key: str, value: Any):
        """Put value in cache"""
        with self.lock:
            if key in self.cache:
                # Remove existing entry
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)
            
            self.cache[key] = value

# Global instances
performance_optimizer = PerformanceOptimizer()
lru_cache = LRUCache(max_size=1000)

# Decorators for performance tracking
def track_performance(operation_name: str = None):
    """Decorator to track function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Operation {operation_name or func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Operation {operation_name or func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

def cache_result(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = lru_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            lru_cache.put(cache_key, result)
            return result
        
        return wrapper
    return decorator

# Utility functions
def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage information"""
    memory = psutil.virtual_memory()
    return {
        'total_gb': memory.total / 1024**3,
        'available_gb': memory.available / 1024**3,
        'used_gb': memory.used / 1024**3,
        'percent': memory.percent
    }

def get_cpu_usage() -> float:
    """Get current CPU usage percentage"""
    return psutil.cpu_percent(interval=1)

def optimize_system():
    """Run system optimization"""
    return performance_optimizer.optimize_memory()
