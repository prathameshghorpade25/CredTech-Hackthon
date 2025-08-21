"""Security utilities for CredTech XScore"""

import hashlib
import secrets
import time
import jwt
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from functools import wraps
import streamlit as st

logger = logging.getLogger(__name__)

class SecurityManager:
    """Central security management for the application"""
    
    def __init__(self):
        self.secret_key = self._generate_secret_key()
        self.jwt_secret = self._generate_jwt_secret()
        self.rate_limits = {}
        self.failed_attempts = {}
        self.suspicious_activities = []
        
        # Security configuration
        self.config = {
            'max_login_attempts': 5,
            'lockout_duration': 900,  # 15 minutes
            'session_timeout': 3600,  # 1 hour
            'password_min_length': 8,
            'require_special_chars': True,
            'max_session_age': 86400,  # 24 hours
            'enable_rate_limiting': True,
            'max_requests_per_minute': 60
        }
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(64)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using secure hashing"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, hash_value = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                salt.encode('utf-8'), 
                100000
            )
            return hash_obj.hex() == hash_value
        except Exception:
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength requirements"""
        errors = []
        
        if len(password) < self.config['password_min_length']:
            errors.append(f"Password must be at least {self.config['password_min_length']} characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if self.config['require_special_chars'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def generate_jwt_token(self, user_data: Dict[str, Any], expires_in: int = None) -> str:
        """Generate a JWT token for user authentication"""
        if expires_in is None:
            expires_in = self.config['session_timeout']
        
        payload = {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'role': user_data.get('role'),
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def check_rate_limit(self, identifier: str, limit: int = None) -> bool:
        """Check if a request is within rate limits"""
        if not self.config['enable_rate_limiting']:
            return True
        
        if limit is None:
            limit = self.config['max_requests_per_minute']
        
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        if identifier in self.rate_limits:
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > minute_ago
            ]
        else:
            self.rate_limits[identifier] = []
        
        # Check if limit exceeded
        if len(self.rate_limits[identifier]) >= limit:
            return False
        
        # Add current request
        self.rate_limits[identifier].append(current_time)
        return True
    
    def check_login_attempts(self, username: str) -> Tuple[bool, int]:
        """Check if user is locked out due to failed login attempts"""
        current_time = time.time()
        
        if username in self.failed_attempts:
            attempts, lockout_until = self.failed_attempts[username]
            
            # Check if still locked out
            if current_time < lockout_until:
                remaining = int(lockout_until - current_time)
                return False, remaining
            
            # Reset if lockout expired
            del self.failed_attempts[username]
        
        return True, 0
    
    def record_failed_login(self, username: str):
        """Record a failed login attempt"""
        current_time = time.time()
        
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            attempts += 1
        else:
            attempts = 1
        
        # Check if should lock out
        if attempts >= self.config['max_login_attempts']:
            lockout_until = current_time + self.config['lockout_duration']
            self.failed_attempts[username] = (attempts, lockout_until)
            
            # Log security event
            self.log_suspicious_activity(
                'multiple_failed_logins',
                f"User {username} locked out after {attempts} failed attempts"
            )
        else:
            self.failed_attempts[username] = (attempts, 0)
    
    def log_suspicious_activity(self, activity_type: str, description: str, metadata: Dict = None):
        """Log suspicious or security-related activities"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'description': description,
            'metadata': metadata or {},
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent()
        }
        
        self.suspicious_activities.append(activity)
        
        # Keep only recent activities
        if len(self.suspicious_activities) > 1000:
            self.suspicious_activities = self.suspicious_activities[-1000:]
        
        logger.warning(f"Suspicious activity detected: {activity_type} - {description}")
    
    def _get_client_ip(self) -> str:
        """Get client IP address from Streamlit session"""
        # This is a simplified version - in production you'd get this from the request
        return st.session_state.get('client_ip', 'unknown')
    
    def _get_user_agent(self) -> str:
        """Get user agent from Streamlit session"""
        # This is a simplified version - in production you'd get this from the request
        return st.session_state.get('user_agent', 'unknown')
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize user input to prevent injection attacks"""
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', '', input_data)
            # Limit length
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            return sanitized
        elif isinstance(input_data, dict):
            return {k: self.sanitize_input(v) for k, v in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def validate_session(self, session_data: Dict[str, Any]) -> bool:
        """Validate session data and check if expired"""
        if not session_data:
            return False
        
        # Check session age
        session_start = session_data.get('created_at')
        if session_start:
            try:
                created_time = datetime.fromisoformat(session_start)
                if datetime.now() - created_time > timedelta(seconds=self.config['max_session_age']):
                    return False
            except ValueError:
                return False
        
        # Check if user is still valid
        user_id = session_data.get('user_id')
        if not user_id:
            return False
        
        return True

# Global security manager instance
security_manager = SecurityManager()

# Security decorators
def require_authentication(func):
    """Decorator to require user authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated'):
            st.error("Authentication required. Please log in.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_role(required_role: str):
    """Decorator to require specific user role"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = st.session_state.get('user_role')
            if user_role != required_role and user_role != 'admin':
                st.error(f"Access denied. Required role: {required_role}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(identifier: str = None, limit: int = None):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as identifier if none provided
            rate_id = identifier or f"{func.__module__}.{func.__name__}"
            
            if not security_manager.check_rate_limit(rate_id, limit):
                st.error("Rate limit exceeded. Please try again later.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def sanitize_inputs(func):
    """Decorator to sanitize function inputs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitize arguments
        sanitized_args = tuple(security_manager.sanitize_input(arg) for arg in args)
        sanitized_kwargs = {k: security_manager.sanitize_input(v) for k, v in kwargs.items()}
        
        return func(*sanitized_args, **sanitized_kwargs)
    return wrapper

# Utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def hash_data(data: str) -> str:
    """Hash data using SHA-256"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no path traversal)"""
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in filename for char in dangerous_chars)