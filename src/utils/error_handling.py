"""Error handling utilities for CredTech XScore"""

import traceback
import functools
import streamlit as st
from typing import Callable, Any, Dict, Optional

from src.utils.logging import get_app_logger

# Set up logger
logger = get_app_logger(__name__)

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    """Exception raised for validation errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 'VALIDATION_ERROR', details)

class AuthenticationError(AppError):
    """Exception raised for authentication errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 'AUTH_ERROR', details)

class DataError(AppError):
    """Exception raised for data processing errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 'DATA_ERROR', details)

class ModelError(AppError):
    """Exception raised for model prediction errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, 'MODEL_ERROR', details)

def handle_error(func: Callable) -> Callable:
    """Decorator to handle errors in Streamlit pages
    
    This decorator catches exceptions, logs them, and displays appropriate error messages
    to the user based on the exception type.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}", extra={'details': e.details})
            st.error(f"⚠️ {e.message}")
            if e.details:
                with st.expander("Details"):
                    for key, value in e.details.items():
                        st.write(f"**{key}:** {value}")
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {e.message}")
            st.error(f"🔒 {e.message}")
            st.warning("Please check your credentials and try again.")
        except DataError as e:
            logger.error(f"Data error: {e.message}", extra={'details': e.details})
            st.error(f"📊 Data Error: {e.message}")
            if e.details:
                with st.expander("Technical Details"):
                    st.json(e.details)
        except ModelError as e:
            logger.error(f"Model error: {e.message}", extra={'details': e.details})
            st.error(f"🤖 Model Error: {e.message}")
            st.info("Our prediction model encountered an issue. The team has been notified.")
            if e.details:
                with st.expander("Technical Details"):
                    st.json(e.details)
        except Exception as e:
            # Unhandled exception
            error_details = traceback.format_exc()
            logger.error(f"Unhandled exception: {str(e)}\n{error_details}")
            st.error("😓 An unexpected error occurred.")
            st.info("The error has been logged and our team will look into it.")
            
            # Show technical details to admin users
            from src.utils.streamlit_auth import get_current_user
            current_user = get_current_user()
            if current_user and current_user.get('role') == 'admin':
                with st.expander("Technical Details"):
                    st.code(error_details)
    
    return wrapper

def api_error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in API endpoints
    
    This decorator catches exceptions and returns appropriate error responses
    with status codes based on the exception type.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"API validation error: {e.message}", extra={'details': e.details})
            return {
                "status": "error",
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }, 400
        except AuthenticationError as e:
            logger.warning(f"API authentication error: {e.message}")
            return {
                "status": "error",
                "error_code": e.error_code,
                "message": e.message
            }, 401
        except DataError as e:
            logger.error(f"API data error: {e.message}", extra={'details': e.details})
            return {
                "status": "error",
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }, 400
        except ModelError as e:
            logger.error(f"API model error: {e.message}", extra={'details': e.details})
            return {
                "status": "error",
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }, 500
        except Exception as e:
            # Unhandled exception
            error_details = traceback.format_exc()
            logger.error(f"API unhandled exception: {str(e)}\n{error_details}")
            return {
                "status": "error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }, 500
    
    return wrapper