"""Structured logging for machine-readable formats and analytics"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from src.utils.enhanced_logging import (
    get_app_logger, get_access_logger, get_error_logger, 
    get_performance_logger, get_interaction_logger, get_security_logger,
    get_session_context, log_with_context
)

# Set up logger
logger = get_app_logger(__name__)

# Constants
STRUCTURED_LOG_DIRECTORY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    'logs', 'structured'
)

# Ensure structured log directory exists
os.makedirs(STRUCTURED_LOG_DIRECTORY, exist_ok=True)

# Define structured log types
LOG_TYPES = {
    'user_activity': os.path.join(STRUCTURED_LOG_DIRECTORY, 'user_activity.jsonl'),
    'performance_metrics': os.path.join(STRUCTURED_LOG_DIRECTORY, 'performance_metrics.jsonl'),
    'security_events': os.path.join(STRUCTURED_LOG_DIRECTORY, 'security_events.jsonl'),
    'model_predictions': os.path.join(STRUCTURED_LOG_DIRECTORY, 'model_predictions.jsonl'),
    'errors': os.path.join(STRUCTURED_LOG_DIRECTORY, 'errors.jsonl'),
    'api_requests': os.path.join(STRUCTURED_LOG_DIRECTORY, 'api_requests.jsonl')
}

def write_structured_log(log_type: str, data: Dict[str, Any]) -> bool:
    """Write structured log data to the appropriate file
    
    Args:
        log_type: Type of log (must be one of LOG_TYPES keys)
        data: Dictionary of log data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if log_type not in LOG_TYPES:
        logger.error(f"Invalid log type: {log_type}. Must be one of {list(LOG_TYPES.keys())}")
        return False
    
    log_file = LOG_TYPES[log_type]
    
    try:
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            
        # Write to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
        return True
    except Exception as e:
        logger.error(f"Failed to write structured log: {str(e)}")
        return False

def log_user_activity(activity_type: str, user_id: str, details: Dict[str, Any]) -> bool:
    """Log user activity in structured format
    
    Args:
        activity_type: Type of activity (e.g., 'login', 'logout', 'view_page', 'button_click')
        user_id: User identifier
        details: Additional activity details
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get session context
    context = get_session_context()
    
    # Create structured log data
    log_data = {
        'activity_type': activity_type,
        'user_id': user_id,
        'session_id': context.get('session_id', ''),
        'ip_address': context.get('ip_address', ''),
        'user_agent': context.get('user_agent', ''),
        'page': context.get('page', ''),
        'details': details
    }
    
    # Write to structured log
    success = write_structured_log('user_activity', log_data)
    
    # Also log to regular logs
    if success:
        log_with_context(
            get_interaction_logger(),
            'info',
            f"User activity: {activity_type} by {user_id}",
            {'activity_details': details}
        )
    
    return success

def log_performance_metric(metric_name: str, value: Union[float, int], 
                          component: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """Log performance metric in structured format
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        component: Component being measured
        details: Additional metric details
        
    Returns:
        bool: True if successful, False otherwise
    """
    if details is None:
        details = {}
    
    # Create structured log data
    log_data = {
        'metric_name': metric_name,
        'value': value,
        'component': component,
        'details': details
    }
    
    # Write to structured log
    success = write_structured_log('performance_metrics', log_data)
    
    # Also log to regular logs
    if success:
        log_with_context(
            get_performance_logger(),
            'info',
            f"Performance metric: {metric_name}={value} for {component}",
            {'metric_details': details}
        )
    
    return success

def log_security_event(event_type: str, severity: str, details: Dict[str, Any]) -> bool:
    """Log security event in structured format
    
    Args:
        event_type: Type of security event
        severity: Severity level ('low', 'medium', 'high', 'critical')
        details: Event details
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get session context
    context = get_session_context()
    
    # Create structured log data
    log_data = {
        'event_type': event_type,
        'severity': severity,
        'session_id': context.get('session_id', ''),
        'ip_address': context.get('ip_address', ''),
        'user_id': context.get('username', ''),
        'details': details
    }
    
    # Write to structured log
    success = write_structured_log('security_events', log_data)
    
    # Also log to regular logs with appropriate level based on severity
    if success:
        level = 'warning' if severity in ['low', 'medium'] else 'error'
        log_with_context(
            get_security_logger(),
            level,
            f"Security event: {event_type} ({severity})",
            {'security_details': details}
        )
    
    return success

def log_model_prediction(model_name: str, input_data: Dict[str, Any], 
                        prediction: Any, confidence: Optional[float] = None,
                        execution_time: Optional[float] = None) -> bool:
    """Log model prediction in structured format
    
    Args:
        model_name: Name of the model
        input_data: Input data for prediction
        prediction: Model prediction result
        confidence: Confidence score (optional)
        execution_time: Execution time in milliseconds (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get session context
    context = get_session_context()
    
    # Create structured log data
    log_data = {
        'model_name': model_name,
        'input_data': input_data,
        'prediction': prediction,
        'session_id': context.get('session_id', ''),
        'user_id': context.get('username', '')
    }
    
    # Add optional fields
    if confidence is not None:
        log_data['confidence'] = confidence
    
    if execution_time is not None:
        log_data['execution_time_ms'] = execution_time
    
    # Write to structured log
    success = write_structured_log('model_predictions', log_data)
    
    # Also log to regular logs
    if success:
        log_with_context(
            get_app_logger(),
            'info',
            f"Model prediction: {model_name} = {prediction}",
            {'prediction_details': log_data}
        )
    
    return success

def log_structured_error(error_type: str, message: str, 
                       details: Optional[Dict[str, Any]] = None,
                       stack_trace: Optional[str] = None) -> bool:
    """Log error in structured format
    
    Args:
        error_type: Type of error
        message: Error message
        details: Additional error details
        stack_trace: Stack trace if available
        
    Returns:
        bool: True if successful, False otherwise
    """
    if details is None:
        details = {}
    
    # Get session context
    context = get_session_context()
    
    # Create structured log data
    log_data = {
        'error_type': error_type,
        'message': message,
        'session_id': context.get('session_id', ''),
        'user_id': context.get('username', ''),
        'page': context.get('page', ''),
        'details': details
    }
    
    # Add stack trace if available
    if stack_trace:
        log_data['stack_trace'] = stack_trace
    
    # Write to structured log
    success = write_structured_log('errors', log_data)
    
    # Also log to regular logs
    if success:
        log_with_context(
            get_error_logger(),
            'error',
            f"Error: {error_type} - {message}",
            {'error_details': details, 'stack_trace': stack_trace}
        )
    
    return success

def log_api_request(endpoint: str, method: str, status_code: int, 
                  response_time: float, request_data: Optional[Dict[str, Any]] = None) -> bool:
    """Log API request in structured format
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        response_time: Response time in milliseconds
        request_data: Request data (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get session context
    context = get_session_context()
    
    # Create structured log data
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time_ms': response_time,
        'session_id': context.get('session_id', ''),
        'user_id': context.get('username', ''),
        'ip_address': context.get('ip_address', '')
    }
    
    # Add request data if available
    if request_data:
        # Remove sensitive data
        if 'password' in request_data:
            request_data['password'] = '[REDACTED]'
        log_data['request_data'] = request_data
    
    # Write to structured log
    success = write_structured_log('api_requests', log_data)
    
    # Also log to regular logs
    if success:
        level = 'error' if status_code >= 400 else 'info'
        log_with_context(
            get_access_logger(),
            level,
            f"API {method} {endpoint} - {status_code} in {response_time:.2f}ms",
            {'api_details': log_data}
        )
    
    return success

def get_structured_logs(log_type: str, limit: int = 100, 
                      filter_func: Optional[callable] = None) -> List[Dict[str, Any]]:
    """Get structured logs of a specific type
    
    Args:
        log_type: Type of log (must be one of LOG_TYPES keys)
        limit: Maximum number of logs to return
        filter_func: Optional function to filter logs
        
    Returns:
        List[Dict[str, Any]]: List of log entries
    """
    if log_type not in LOG_TYPES:
        logger.error(f"Invalid log type: {log_type}. Must be one of {list(LOG_TYPES.keys())}")
        return []
    
    log_file = LOG_TYPES[log_type]
    
    if not os.path.exists(log_file):
        return []
    
    try:
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if filter_func is None or filter_func(log_entry):
                        logs.append(log_entry)
                        if len(logs) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        return logs
    except Exception as e:
        logger.error(f"Failed to read structured logs: {str(e)}")
        return []

def aggregate_metrics(metric_name: str, time_window_minutes: int = 60) -> Dict[str, Any]:
    """Aggregate performance metrics over a time window
    
    Args:
        metric_name: Name of the metric to aggregate
        time_window_minutes: Time window in minutes
        
    Returns:
        Dict[str, Any]: Aggregated metrics
    """
    # Calculate time threshold
    time_threshold = datetime.now().timestamp() - (time_window_minutes * 60)
    
    # Get performance metrics
    metrics = get_structured_logs('performance_metrics')
    
    # Filter by metric name and time window
    filtered_metrics = []
    for metric in metrics:
        try:
            metric_time = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00')).timestamp()
            if metric['metric_name'] == metric_name and metric_time >= time_threshold:
                filtered_metrics.append(metric)
        except (KeyError, ValueError):
            continue
    
    # Calculate aggregates
    if not filtered_metrics:
        return {
            'metric_name': metric_name,
            'count': 0,
            'min': None,
            'max': None,
            'avg': None,
            'time_window_minutes': time_window_minutes
        }
    
    values = [m['value'] for m in filtered_metrics if 'value' in m]
    
    return {
        'metric_name': metric_name,
        'count': len(values),
        'min': min(values) if values else None,
        'max': max(values) if values else None,
        'avg': sum(values) / len(values) if values else None,
        'time_window_minutes': time_window_minutes
    }