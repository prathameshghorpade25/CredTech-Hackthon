"""Middleware utilities for CredTech XScore API"""

import time
from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.monitoring import record_request, record_response_time, record_error


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API requests and responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract endpoint path for metrics
        endpoint = request.url.path
        
        # Record the request
        record_request(endpoint)
        
        # Measure response time
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Record response time
            response_time = time.time() - start_time
            record_response_time(endpoint, response_time)
            
            # Add response time header for debugging
            response.headers["X-Response-Time"] = str(response_time)
            
            return response
        except Exception as e:
            # Record error
            record_error(endpoint)
            
            # Re-raise the exception
            raise e


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""
    
    def __init__(self, app: ASGIApp, rate_limit: int = 100, window_size: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit  # requests per window
        self.window_size = window_size  # window size in seconds
        self.request_counts: Dict[str, Dict[float, int]] = {}  # {ip: {timestamp: count}}
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if the client IP is rate limited"""
        current_time = time.time()
        
        # Initialize if this is the first request from this IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {current_time: 1}
            return False
        
        # Clean up old timestamps
        self.request_counts[client_ip] = {
            ts: count for ts, count in self.request_counts[client_ip].items()
            if current_time - ts < self.window_size
        }
        
        # Count requests in the current window
        total_requests = sum(self.request_counts[client_ip].values())
        
        # Check if rate limit is exceeded
        if total_requests >= self.rate_limit:
            return True
        
        # Increment request count
        if current_time in self.request_counts[client_ip]:
            self.request_counts[client_ip][current_time] += 1
        else:
            self.request_counts[client_ip][current_time] = 1
        
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if rate limited
        if self._is_rate_limited(client_ip):
            # Return 429 Too Many Requests
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.window_size)}
            )
        
        # Process the request
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses"""
    
    def __init__(self, app: ASGIApp, logger=None):
        super().__init__(app)
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request
        request_id = str(time.time())
        client_ip = request.client.host if request.client else "unknown"
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "headers": dict(request.headers),
        }
        
        if self.logger:
            self.logger.info(f"Request: {request_info}")
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        response_info = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time,
            "headers": dict(response.headers),
        }
        
        if self.logger:
            self.logger.info(f"Response: {response_info}")
        
        # Add request ID to response headers for tracking
        response.headers["X-Request-ID"] = request_id
        
        return response


def add_monitoring_middleware(app: FastAPI, logger=None):
    """Add monitoring middleware to FastAPI app"""
    app.add_middleware(MonitoringMiddleware)
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
    
    # Rate limiting for scoring endpoints
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit=100,  # 100 requests per minute
        window_size=60,  # 1 minute window
    )
    
    return app