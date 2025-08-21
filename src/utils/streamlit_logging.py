"""Streamlit-specific logging utilities for CredTech XScore"""

import time
import json
import traceback
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Union, List, Callable

import streamlit as st

from src.utils.enhanced_logging import (
    get_app_logger,
    get_access_logger,
    get_interaction_logger,
    get_error_logger,
    get_security_logger,
    get_session_context,
    log_with_context
)

# Set up loggers
logger = get_app_logger(__name__)
interaction_logger = get_interaction_logger()
security_logger = get_security_logger()

# Component interaction logging functions
def log_button_click(button_name: str, page: Optional[str] = None):
    """Log a button click interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Button clicked: {button_name}",
        extra={
            'extra': {
                'interaction_type': 'button_click',
                'component': 'button',
                'component_name': button_name,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_slider_change(slider_name: str, value: Any, page: Optional[str] = None):
    """Log a slider change interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Slider changed: {slider_name} = {value}",
        extra={
            'extra': {
                'interaction_type': 'slider_change',
                'component': 'slider',
                'component_name': slider_name,
                'value': str(value),
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_input_change(input_name: str, value_type: str, page: Optional[str] = None):
    """Log an input change interaction (without logging the actual value for privacy)"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Input changed: {input_name}",
        extra={
            'extra': {
                'interaction_type': 'input_change',
                'component': 'input',
                'component_name': input_name,
                'value_type': value_type,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_selectbox_change(selectbox_name: str, value: Any, page: Optional[str] = None):
    """Log a selectbox change interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Selectbox changed: {selectbox_name} = {value}",
        extra={
            'extra': {
                'interaction_type': 'selectbox_change',
                'component': 'selectbox',
                'component_name': selectbox_name,
                'value': str(value),
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_checkbox_change(checkbox_name: str, value: bool, page: Optional[str] = None):
    """Log a checkbox change interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Checkbox changed: {checkbox_name} = {value}",
        extra={
            'extra': {
                'interaction_type': 'checkbox_change',
                'component': 'checkbox',
                'component_name': checkbox_name,
                'value': value,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_file_upload(file_name: str, file_size: int, file_type: str, page: Optional[str] = None):
    """Log a file upload interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"File uploaded: {file_name}",
        extra={
            'extra': {
                'interaction_type': 'file_upload',
                'component': 'file_uploader',
                'file_name': file_name,
                'file_size': file_size,
                'file_type': file_type,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_page_view(page_name: str):
    """Log a page view interaction"""
    context = get_session_context()
    
    interaction_logger.info(
        f"Page viewed: {page_name}",
        extra={
            'extra': {
                'interaction_type': 'page_view',
                'page': page_name,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_tab_change(tab_group: str, tab_name: str, page: Optional[str] = None):
    """Log a tab change interaction"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    interaction_logger.info(
        f"Tab changed: {tab_group} -> {tab_name}",
        extra={
            'extra': {
                'interaction_type': 'tab_change',
                'component': 'tabs',
                'tab_group': tab_group,
                'tab_name': tab_name,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_chart_interaction(chart_name: str, interaction_type: str, details: Dict[str, Any] = None, page: Optional[str] = None):
    """Log a chart interaction (zoom, pan, click, etc.)"""
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    if details is None:
        details = {}
    
    interaction_logger.info(
        f"Chart interaction: {chart_name} - {interaction_type}",
        extra={
            'extra': {
                'interaction_type': 'chart_interaction',
                'component': 'chart',
                'chart_name': chart_name,
                'chart_interaction_type': interaction_type,
                'details': details,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

# Performance tracking for Streamlit components
def log_component_render_time(component_name: str, render_time_ms: float, page: Optional[str] = None):
    """Log the render time for a Streamlit component"""
    from src.utils.enhanced_logging import get_performance_logger
    performance_logger = get_performance_logger()
    
    context = get_session_context()
    if page is None and 'page' in st.session_state:
        page = st.session_state['page']
    
    performance_logger.info(
        f"Component render: {component_name} took {render_time_ms:.2f}ms",
        extra={
            'extra': {
                'component': component_name,
                'render_time_ms': render_time_ms,
                'page': page,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

# Decorator to measure and log component render time
def measure_render_time(component_name: str):
    """Decorator to measure and log the render time of a function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            render_time_ms = (end_time - start_time) * 1000
            
            # Log the render time
            log_component_render_time(component_name, render_time_ms)
            
            return result
        return wrapper
    return decorator

# Security logging functions
def log_authentication_attempt(username: str, success: bool, ip_address: Optional[str] = None):
    """Log an authentication attempt"""
    context = get_session_context()
    
    # Don't log the username if authentication failed (security best practice)
    if not success:
        username = "[redacted]"
    
    security_logger.info(
        f"Authentication attempt: {'Success' if success else 'Failure'}",
        extra={
            'extra': {
                'event_type': 'authentication',
                'username': username,
                'success': success,
                'ip_address': ip_address,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_authorization_check(resource: str, action: str, allowed: bool):
    """Log an authorization check"""
    context = get_session_context()
    
    security_logger.info(
        f"Authorization check: {action} on {resource} - {'Allowed' if allowed else 'Denied'}",
        extra={
            'extra': {
                'event_type': 'authorization',
                'resource': resource,
                'action': action,
                'allowed': allowed,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log a general security event"""
    context = get_session_context()
    
    security_logger.info(
        f"Security event: {event_type}",
        extra={
            'extra': {
                'event_type': event_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            },
            'context': context
        }
    )

# Initialize logging when this module is imported
logger.info("Streamlit logging utilities initialized")