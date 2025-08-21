import logging
import os
import json
import time
import traceback
import platform
import socket
import uuid
import sys
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any, Optional, Union, List

# Import custom log rotation handler
from src.utils.log_rotation import CompressedRotatingFileHandler, setup_log_rotation, schedule_log_maintenance

# Constants
LOG_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
APP_LOG_FILE = os.path.join(LOG_DIRECTORY, 'app.log')
ACCESS_LOG_FILE = os.path.join(LOG_DIRECTORY, 'access.log')
ERROR_LOG_FILE = os.path.join(LOG_DIRECTORY, 'error.log')
PERFORMANCE_LOG_FILE = os.path.join(LOG_DIRECTORY, 'performance.log')
INTERACTION_LOG_FILE = os.path.join(LOG_DIRECTORY, 'interaction.log')
SECURITY_LOG_FILE = os.path.join(LOG_DIRECTORY, 'security.log')

# Generate a unique instance ID for this application instance
APP_INSTANCE_ID = str(uuid.uuid4())

# Get system information
SYSTEM_INFO = {
    'hostname': socket.gethostname(),
    'platform': platform.platform(),
    'python_version': platform.python_version(),
    'processor': platform.processor(),
    'instance_id': APP_INSTANCE_ID,
    'start_time': datetime.now().isoformat()
}

# Ensure log directory exists
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Custom formatter for structured logging
class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis"""
    def __init__(self, include_system_info=True):
        super().__init__()
        self.include_system_info = include_system_info
        
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'app_instance': APP_INSTANCE_ID
        }
        
        # Add system info if configured
        if self.include_system_info:
            log_data['system'] = SYSTEM_INFO
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # Add extra fields if available
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        # Add context data if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
            
        return json.dumps(log_data)

# Setup main application logger
def setup_logger(name, log_file=APP_LOG_FILE, level=logging.INFO, json_format=True):
    """Set up a logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler with rotation and compression (10MB max size, keep 10 backups)
    file_handler = CompressedRotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Setup access logger for tracking user interactions
def setup_access_logger():
    """Set up a specialized logger for tracking user access and actions"""
    logger = logging.getLogger('credtech.access')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Use time-based rotation (daily)
    handler = TimedRotatingFileHandler(
        ACCESS_LOG_FILE, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Setup error logger
def setup_error_logger():
    """Set up a specialized logger for errors only"""
    logger = logging.getLogger('credtech.error')
    logger.setLevel(logging.ERROR)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
    )
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Setup performance logger
def setup_performance_logger():
    """Set up a specialized logger for performance metrics"""
    logger = logging.getLogger('credtech.performance')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = RotatingFileHandler(
        PERFORMANCE_LOG_FILE, maxBytes=10*1024*1024, backupCount=10, encoding='utf-8'
    )
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Setup interaction logger
def setup_interaction_logger():
    """Set up a specialized logger for detailed user interactions"""
    logger = logging.getLogger('credtech.interaction')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = RotatingFileHandler(
        INTERACTION_LOG_FILE, maxBytes=20*1024*1024, backupCount=20, encoding='utf-8'
    )
    formatter = JsonFormatter(include_system_info=False)  # Don't include system info in every interaction log
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Setup security logger
def setup_security_logger():
    """Set up a specialized logger for security events"""
    logger = logging.getLogger('credtech.security')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = RotatingFileHandler(
        SECURITY_LOG_FILE, maxBytes=10*1024*1024, backupCount=30, encoding='utf-8'
    )
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Enhanced logging configuration with log levels and handlers
def setup_advanced_logging(name, log_file=APP_LOG_FILE, level=logging.INFO, json_format=True, 
                          max_bytes=10*1024*1024, backup_count=10, enable_console=True):
    """Set up an advanced logger with multiple handlers and rotation"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    # File handler with rotation and compression
    file_handler = CompressedRotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for development
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Error handler for critical errors
    error_handler = CompressedRotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=max_bytes, backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Performance handler for timing logs
    perf_handler = CompressedRotatingFileHandler(
        PERFORMANCE_LOG_FILE, maxBytes=max_bytes, backupCount=backup_count
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(formatter)
    logger.addHandler(perf_handler)
    
    return logger

# Enhanced context manager for logging
class LogContext:
    """Context manager for structured logging with automatic context tracking"""
    
    def __init__(self, logger, context_data=None):
        self.logger = logger
        self.context_data = context_data or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        # Add context to logger
        if hasattr(self.logger, 'context'):
            self.logger.context = self.context_data
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.context_data['duration_ms'] = round(duration * 1000, 2)
            
            if exc_type:
                self.logger.error(
                    f"Context execution failed after {duration:.2f}s",
                    extra={'context': self.context_data, 'exception': str(exc_val)}
                )
            else:
                self.logger.info(
                    f"Context executed successfully in {duration:.2f}s",
                    extra={'context': self.context_data}
                )

# Enhanced performance tracking decorator
def track_performance(operation_name=None, log_args=True, log_result=False):
    """Enhanced decorator to track function performance with detailed metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            # Log function entry with context
            context = {
                'operation': op_name,
                'function': f"{func.__module__}.{func.__name__}",
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }
            
            if log_args and args:
                context['args_types'] = [type(arg).__name__ for arg in args]
            if log_args and kwargs:
                context['kwargs_keys'] = list(kwargs.keys())
            
            logger = get_app_logger(func.__module__)
            logger.info(f"Starting operation: {op_name}", extra={'context': context})
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful completion
                success_context = {
                    **context,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'success'
                }
                
                if log_result and result is not None:
                    success_context['result_type'] = type(result).__name__
                    if hasattr(result, '__len__'):
                        success_context['result_length'] = len(result)
                
                logger.info(f"Operation completed: {op_name}", extra={'context': success_context})
                
                # Log performance metric
                log_performance_metric(
                    metric_name="function_execution_time",
                    value=execution_time,
                    unit="seconds",
                    context=success_context
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_context = {
                    **context,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'error',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
                
                logger.error(f"Operation failed: {op_name}", extra={'context': error_context})
                
                # Log error metric
                log_structured_error(
                    error_type="function_execution_error",
                    error_message=str(e),
                    source=op_name,
                    context=error_context
                )
                
                raise
                
        return wrapper
    return decorator

# Enhanced session tracking
class SessionTracker:
    """Enhanced session tracking with detailed analytics"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.start_time = time.time()
        self.actions = []
        self.page_views = []
        self.errors = []
        self.performance_metrics = {}
        
    def log_action(self, action_type, details=None, duration=None):
        """Log a user action with timing"""
        action = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'details': details or {},
            'duration_ms': duration
        }
        self.actions.append(action)
        
        # Log to structured logging
        log_user_activity(
            user_id=st.session_state.get('username', 'anonymous'),
            activity_type=action_type,
            details={
                'session_id': self.session_id,
                'action_details': details,
                'duration_ms': duration
            }
        )
    
    def log_page_view(self, page_name, metadata=None):
        """Log a page view with metadata"""
        page_view = {
            'timestamp': datetime.now().isoformat(),
            'page_name': page_name,
            'metadata': metadata or {}
        }
        self.page_views.append(page_view)
        
        # Log to structured logging
        log_page_view(page_name, metadata or {})
    
    def log_error(self, error_type, error_message, context=None):
        """Log an error with context"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        }
        self.errors.append(error)
        
        # Log to structured logging
        log_structured_error(
            error_type=error_type,
            error_message=error_message,
            source='session',
            context={
                'session_id': self.session_id,
                **(context or {})
            }
        )
    
    def get_session_summary(self):
        """Get a summary of the session"""
        duration = time.time() - self.start_time
        return {
            'session_id': self.session_id,
            'duration_seconds': round(duration, 2),
            'total_actions': len(self.actions),
            'total_page_views': len(self.page_views),
            'total_errors': len(self.errors),
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat()
        }

# Convenience function to get the main application logger
def get_app_logger(name):
    """Get the application logger with the given name"""
    return setup_logger(f'credtech.{name}')

# Convenience function to get the access logger
def get_access_logger():
    """Get the access logger for tracking user interactions"""
    return setup_access_logger()

# Convenience function to get the error logger
def get_error_logger():
    """Get the error logger for tracking errors"""
    return setup_error_logger()

# Convenience function to get the performance logger
def get_performance_logger():
    """Get the performance logger for tracking performance metrics"""
    return setup_performance_logger()

# Convenience function to get the interaction logger
def get_interaction_logger():
    """Get the interaction logger for tracking detailed user interactions"""
    return setup_interaction_logger()

# Convenience function to get the security logger
def get_security_logger():
    """Get the security logger for tracking security events"""
    return setup_security_logger()

# Convenience function to log security events
def log_security_event(event_type, message, user_id=None, ip_address=None, context=None):
    """Log a security event with structured information"""
    security_logger = get_security_logger()
    
    extra_data = {
        'extra': {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat(),
            **(context or {})
        }
    }
    
    security_logger.warning(
        f"SECURITY EVENT: {event_type} - {message}",
        extra=extra_data
    )

# Decorator for logging function calls
def log_function_call(logger=None):
    """Decorator to log function calls with parameters and return values"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided logger or get default app logger
            log = logger or get_app_logger(func.__module__)
            
            # Log function call
            log.debug(
                f"Calling {func.__name__}", 
                extra={
                    'extra': {
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                }
            )
            
            # Measure execution time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful execution
                log.debug(
                    f"{func.__name__} completed in {execution_time:.4f}s",
                    extra={
                        'extra': {
                            'function': func.__name__,
                            'execution_time': execution_time,
                            'result_type': type(result).__name__
                        }
                    }
                )
                
                # Log performance metrics for slow functions (> 1 second)
                if execution_time > 1.0:
                    perf_logger = get_performance_logger()
                    perf_logger.info(
                        f"Slow function: {func.__name__} took {execution_time:.4f}s",
                        extra={
                            'extra': {
                                'function': func.__name__,
                                'execution_time': execution_time,
                                'args': str(args),
                                'kwargs': str(kwargs)
                            }
                        }
                    )
                
                return result
            except Exception as e:
                # Log exception
                execution_time = time.time() - start_time
                log.exception(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={
                        'extra': {
                            'function': func.__name__,
                            'execution_time': execution_time,
                            'exception': str(e),
                            'args': str(args),
                            'kwargs': str(kwargs)
                        }
                    }
                )
                
                # Also log to error logger
                error_logger = get_error_logger()
                error_logger.exception(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={
                        'extra': {
                            'function': func.__name__,
                            'execution_time': execution_time,
                            'exception': str(e),
                            'args': str(args),
                            'kwargs': str(kwargs)
                        }
                    }
                )
                
                raise
        return wrapper
    return decorator

# Function to get session context information
def get_session_context():
    """Get context information about the current user session"""
    context = {
        'timestamp': datetime.now().isoformat(),
        'app_instance': APP_INSTANCE_ID
    }
    
    try:
        import streamlit as st
        # Add session ID if available
        try:
            if 'session_id' in st.session_state:
                context['session_id'] = st.session_state['session_id']
            else:
                # Generate a new session ID if not present
                st.session_state['session_id'] = str(uuid.uuid4())
                context['session_id'] = st.session_state['session_id']
                context['new_session'] = True
        except Exception:
            # If session state is not available (e.g., outside Streamlit runtime)
            context['session_id'] = str(uuid.uuid4())
            context['session_state_available'] = False
        
        # Add user information if available
        try:
            if 'user' in st.session_state and st.session_state['user']:
                user = st.session_state['user']
                context['user'] = {
                    'username': user.get('username', 'Unknown'),
                    'role': user.get('role', 'Unknown'),
                    'last_login': user.get('last_login', 'Unknown')
                }
            else:
                context['user'] = 'Anonymous'
        except Exception:
            context['user'] = 'Anonymous'
            context['session_state_available'] = False
            
        # Add page information if available
        try:
            if 'page' in st.session_state:
                context['page'] = st.session_state['page']
        except Exception:
            pass
            
        # Add query parameters if available
        try:
            query_params = st.experimental_get_query_params()
            if query_params:
                context['query_params'] = query_params
        except Exception:
            # Silently continue if query parameters can't be accessed
            pass
            
    except ImportError:
        context['streamlit_available'] = False
        
    return context

# Log with context information
def log_with_context(logger, level, message, context=None, extra=None):
    """Log a message with context information"""
    if context is None:
        context = get_session_context()
        
    if extra is None:
        extra = {}
        
    # Combine context and extra
    combined_extra = {'context': context}
    if extra:
        combined_extra['extra'] = extra
        
    # Log with the appropriate level
    if level.lower() == 'debug':
        logger.debug(message, extra=combined_extra)
    elif level.lower() == 'info':
        logger.info(message, extra=combined_extra)
    elif level.lower() == 'warning':
        logger.warning(message, extra=combined_extra)
    elif level.lower() == 'error':
        logger.error(message, extra=combined_extra)
    elif level.lower() == 'critical':
        logger.critical(message, extra=combined_extra)
    else:
        logger.info(message, extra=combined_extra)

# Decorator for logging user actions in Streamlit
def log_user_action(action_type):
    """Decorator to log user actions in the Streamlit app"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get access logger and interaction logger
            access_logger = get_access_logger()
            interaction_logger = get_interaction_logger()
            
            # Get session context
            context = get_session_context()
            user_info = context.get('user', 'Anonymous')
            
            # Log the action to access log
            access_logger.info(
                f"User action: {action_type}",
                extra={
                    'extra': {
                        'action_type': action_type,
                        'user': user_info,
                        'function': func.__name__,
                        'timestamp': datetime.now().isoformat()
                    },
                    'context': context
                }
            )
            
            # Log more detailed information to interaction log
            interaction_logger.info(
                f"User interaction: {action_type} - {func.__name__}",
                extra={
                    'extra': {
                        'action_type': action_type,
                        'user': user_info,
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs),
                        'timestamp': datetime.now().isoformat()
                    },
                    'context': context
                }
            )
            
            # Execute the function
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Initialize all loggers at module import
app_logger = get_app_logger('app')
access_logger = get_access_logger()
error_logger = get_error_logger()
performance_logger = get_performance_logger()
interaction_logger = get_interaction_logger()
security_logger = get_security_logger()

# Initialize log rotation and archiving
def initialize_log_rotation():
    """Initialize log rotation and archiving for all log files"""
    # Schedule log maintenance for all log files
    try:
        # Create archive directory if it doesn't exist
        archive_dir = os.path.join(LOG_DIRECTORY, 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        
        # Schedule log maintenance (archive logs older than 30 days, remove archives older than 365 days)
        schedule_log_maintenance(LOG_DIRECTORY, archive_dir, archive_days=30, cleanup_days=365)
        
        # Log successful initialization
        app_logger.info(f"Log rotation and archiving initialized. Archive directory: {archive_dir}")
    except Exception as e:
        # Log error but don't crash the application
        app_logger.error(f"Failed to initialize log rotation: {str(e)}")
        app_logger.error(traceback.format_exc())

# Initialize log rotation
initialize_log_rotation()

# Log application startup with system context
app_logger.info(
    "Enhanced logging system initialized", 
    extra={
        'extra': {
            'system_info': SYSTEM_INFO,
            'log_files': {
                'app': APP_LOG_FILE,
                'access': ACCESS_LOG_FILE,
                'error': ERROR_LOG_FILE,
                'performance': PERFORMANCE_LOG_FILE,
                'interaction': INTERACTION_LOG_FILE,
                'security': SECURITY_LOG_FILE
            }
        }
    }
)