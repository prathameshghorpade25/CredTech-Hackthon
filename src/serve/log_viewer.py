"""Log viewer component for the Streamlit dashboard"""

import streamlit as st
import pandas as pd
import os
import json
import glob
import datetime
from typing import List, Dict, Any, Optional

from src.utils.enhanced_logging import (
    get_app_logger, get_access_logger, get_error_logger, 
    get_performance_logger, get_interaction_logger, get_security_logger,
    APP_LOG_FILE, ACCESS_LOG_FILE, ERROR_LOG_FILE, 
    PERFORMANCE_LOG_FILE, INTERACTION_LOG_FILE, SECURITY_LOG_FILE
)
from src.utils.streamlit_auth import require_auth
from src.utils.streamlit_logging import log_button_click, log_selectbox_change

# Set up logger
logger = get_app_logger(__name__)

# Constants
MAX_LOGS_TO_DISPLAY = 1000
LOG_TYPES = {
    "Application": APP_LOG_FILE,
    "Access": ACCESS_LOG_FILE,
    "Error": ERROR_LOG_FILE,
    "Performance": PERFORMANCE_LOG_FILE,
    "Interaction": INTERACTION_LOG_FILE,
    "Security": SECURITY_LOG_FILE
}

def read_log_file(log_file: str, n_lines: int = MAX_LOGS_TO_DISPLAY) -> List[Dict[str, Any]]:
    """Read and parse JSON log file
    
    Args:
        log_file: Path to log file
        n_lines: Maximum number of lines to read (most recent first)
        
    Returns:
        List of parsed log entries as dictionaries
    """
    try:
        if not os.path.exists(log_file):
            logger.warning(f"Log file not found: {log_file}")
            return []
        
        # Read log file (each line is a JSON object)
        with open(log_file, 'r') as f:
            # Read all lines and take the last n_lines
            lines = f.readlines()
            lines = lines[-n_lines:] if len(lines) > n_lines else lines
        
        # Parse JSON entries
        logs = []
        for line in lines:
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        return logs
    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {str(e)}")
        return []

def get_log_files(log_type: str = None) -> List[str]:
    """Get list of log files for a specific type or all types
    
    Args:
        log_type: Log type to filter by (or None for all)
        
    Returns:
        List of log file paths
    """
    if log_type and log_type in LOG_TYPES:
        # Get specific log file and any rotated versions
        log_file = LOG_TYPES[log_type]
        base_dir = os.path.dirname(log_file)
        base_name = os.path.basename(log_file)
        return glob.glob(f"{base_dir}/{base_name}*")
    else:
        # Get all log files
        all_files = []
        for log_file in LOG_TYPES.values():
            base_dir = os.path.dirname(log_file)
            base_name = os.path.basename(log_file)
            all_files.extend(glob.glob(f"{base_dir}/{base_name}*"))
        return all_files

def filter_logs(logs: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter logs based on criteria
    
    Args:
        logs: List of log entries
        filters: Dictionary of filter criteria
        
    Returns:
        Filtered list of log entries
    """
    filtered_logs = logs
    
    # Apply filters
    for key, value in filters.items():
        if not value:  # Skip empty filters
            continue
            
        # Handle nested fields with dot notation (e.g., "context.username")
        if '.' in key:
            parts = key.split('.')
            filtered_logs = [
                log for log in filtered_logs 
                if all_parts_exist(log, parts) and 
                get_nested_value(log, parts).lower().find(value.lower()) >= 0
            ]
        else:
            # Direct field filter
            filtered_logs = [
                log for log in filtered_logs 
                if key in log and 
                str(log[key]).lower().find(value.lower()) >= 0
            ]
    
    return filtered_logs

def all_parts_exist(d: Dict[str, Any], parts: List[str]) -> bool:
    """Check if all nested parts exist in dictionary"""
    current = d
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            return False
        current = current[part]
    return parts[-1] in current

def get_nested_value(d: Dict[str, Any], parts: List[str]) -> Any:
    """Get value from nested dictionary using parts list"""
    current = d
    for part in parts[:-1]:
        current = current[part]
    return str(current[parts[-1]])

@require_auth
def log_viewer_page():
    """Admin log viewer page"""
    st.title("Log Viewer")
    
    # Check if user is admin
    if not st.session_state.get("user") or st.session_state["user"].get("role") != "admin":
        st.error("You do not have permission to view this page.")
        return
    
    # Log type selection
    log_type = st.selectbox(
        "Select Log Type",
        list(LOG_TYPES.keys()),
        key="log_type_selector"
    )
    log_selectbox_change("log_type_selector", log_type, {"available_options": list(LOG_TYPES.keys())})
    
    # Get log file path
    log_file = LOG_TYPES.get(log_type)
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            datetime.datetime.now().date() - datetime.timedelta(days=7)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            datetime.datetime.now().date()
        )
    
    # Additional filters
    with st.expander("Advanced Filters"):
        level_filter = st.selectbox(
            "Log Level",
            ["", "debug", "info", "warning", "error", "critical"],
            key="level_filter"
        )
        
        message_filter = st.text_input("Message Contains", key="message_filter")
        
        # User filter (for access and security logs)
        if log_type in ["Access", "Security", "Interaction"]:
            user_filter = st.text_input("Username Contains", key="user_filter")
        else:
            user_filter = ""
        
        # Session filter
        session_filter = st.text_input("Session ID Contains", key="session_filter")
    
    # Read logs
    if st.button("Load Logs", key="load_logs_button"):
        log_button_click("load_logs_button", {"log_type": log_type})
        
        with st.spinner("Loading logs..."):
            # Read log file
            logs = read_log_file(log_file)
            
            if not logs:
                st.warning(f"No logs found in {log_file}")
                return
            
            # Convert timestamps to datetime for filtering
            for log in logs:
                if "timestamp" in log:
                    try:
                        log["datetime"] = datetime.datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        log["datetime"] = datetime.datetime.now()  # Fallback
            
            # Apply date filter
            start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
            
            logs = [log for log in logs if start_datetime <= log.get("datetime", datetime.datetime.now()) <= end_datetime]
            
            # Apply other filters
            filters = {}
            if level_filter:
                filters["level"] = level_filter
            if message_filter:
                filters["message"] = message_filter
            if user_filter:
                filters["context.username"] = user_filter
            if session_filter:
                filters["context.session_id"] = session_filter
            
            filtered_logs = filter_logs(logs, filters)
            
            # Display logs
            if not filtered_logs:
                st.warning("No logs match the selected filters")
                return
            
            # Convert to DataFrame for display
            log_records = []
            for log in filtered_logs:
                record = {
                    "timestamp": log.get("timestamp", ""),
                    "level": log.get("level", ""),
                    "message": log.get("message", ""),
                }
                
                # Add context fields if available
                context = log.get("context", {})
                if context:
                    if "username" in context:
                        record["username"] = context["username"]
                    if "session_id" in context:
                        record["session_id"] = context["session_id"]
                    if "page" in context:
                        record["page"] = context["page"]
                
                log_records.append(record)
            
            df = pd.DataFrame(log_records)
            
            # Display as table
            st.dataframe(df, use_container_width=True)
            
            # Show log count
            st.info(f"Displaying {len(filtered_logs)} of {len(logs)} logs")
            
            # Export option
            if st.button("Export to CSV", key="export_logs_button"):
                log_button_click("export_logs_button", {"log_type": log_type, "count": len(filtered_logs)})
                
                # Convert to CSV
                csv = df.to_csv(index=False)
                
                # Create download button
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{log_type.lower()}_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Display log file information
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file) / 1024  # KB
        file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
        
        st.sidebar.subheader("Log File Information")
        st.sidebar.info(
            f"**File:** {os.path.basename(log_file)}  \n"
            f"**Size:** {file_size:.2f} KB  \n"
            f"**Last Modified:** {file_modified.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Show rotated log files if they exist
        rotated_files = get_log_files(log_type)
        if len(rotated_files) > 1:  # More than just the current log file
            st.sidebar.subheader("Rotated Log Files")
            for rf in rotated_files:
                if rf != log_file:  # Skip current file
                    rf_size = os.path.getsize(rf) / 1024  # KB
                    rf_modified = datetime.datetime.fromtimestamp(os.path.getmtime(rf))
                    st.sidebar.text(
                        f"{os.path.basename(rf)}\n"
                        f"Size: {rf_size:.2f} KB\n"
                        f"Modified: {rf_modified.strftime('%Y-%m-%d')}"
                    )