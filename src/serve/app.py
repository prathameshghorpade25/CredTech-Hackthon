import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import joblib
import time
import traceback
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Any, Optional, Union

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))  

# Import from the new simplified model file
from src.model.credit_score_model import CreditScoreModel
from src.features.processor import FeatureProcessor
from src.utils.io import load_model
from src.utils.enhanced_logging import get_app_logger, get_access_logger, log_function_call, log_user_action, get_session_context, log_with_context, log_security_event
from src.utils.streamlit_logging import (
    log_button_click, log_slider_change, log_input_change, log_selectbox_change,
    log_checkbox_change, log_file_upload, log_page_view, log_tab_change,
    log_chart_interaction, log_component_render_time, measure_render_time,
    log_authentication_attempt, log_authorization_check, log_security_event as log_structured_security_event
)
from src.utils.structured_logging import (
    log_user_activity, log_performance_metric, log_security_event as log_structured_error,
    log_model_prediction, log_structured_error, log_api_request
)
from src.utils.streamlit_auth import is_authenticated, display_login_form, logout_user, get_current_user, require_auth
# Import validation and error handling utilities
from src.utils.validation import (
    ValidationResult,
    validate_not_empty,
    validate_range,
    validate_regex,
    validate_enum,
    validate_email,
    validate_password_strength,
    sanitize_input,
    sanitize_dict
)

from src.utils.error_handling import (
    handle_error,
    ValidationError,
    AuthenticationError,
    DataError,
    ModelError
)
# Import monitoring utilities with error handling
try:
    from src.utils.monitoring import start_monitoring, stop_monitoring, record_request, record_response_time, record_error, record_user_login, record_user_logout, record_prediction, get_current_metrics, get_recent_alerts
    monitoring_available = True
except ImportError as e:
    print(f"Warning: Monitoring module not fully available: {e}")
    monitoring_available = False
    
    # Define dummy functions to prevent errors
    def start_monitoring(collection_interval=60): pass
    def stop_monitoring(): pass
    def record_request(endpoint): 
        # Log structured API request
        log_api_request(
            endpoint=endpoint,
            method="GET",
            status_code=200,
            user_id=st.session_state.get('username', 'anonymous'),
            session_id=st.session_state.get('session_id', 'unknown')
        )
    def record_response_time(endpoint, response_time): 
        # Log structured performance metric
        log_performance_metric(
            metric_name="response_time",
            value=response_time,
            unit="ms",
            context={
                "endpoint": endpoint,
                "session_id": st.session_state.get('session_id', 'unknown')
            }
        )
    def record_error(endpoint): 
        # Log structured error
        log_structured_error(
            error_type="application_error",
            error_message=f"Error in {endpoint}",
            source=endpoint,
            context={
                "session_id": st.session_state.get('session_id', 'unknown'),
                "user": st.session_state.get('username', 'anonymous')
            }
        )
    def record_user_login(): 
        # Log structured user activity
        log_user_activity(
            user_id=st.session_state.get('username', 'anonymous'),
            activity_type="login",
            details={
                "session_id": st.session_state.get('session_id', 'unknown')
            }
        )
    
    def record_user_logout(): 
        # Log structured user activity
        log_user_activity(
            user_id=st.session_state.get('username', 'anonymous'),
            activity_type="logout",
            details={
                "session_id": st.session_state.get('session_id', 'unknown')
            }
        )
    def record_prediction(model_version, latency): 
        # Log structured performance metric
        log_performance_metric(
            metric_name="model_prediction_latency",
            value=latency,
            unit="ms",
            context={
                "model_version": model_version
            }
        )
    def get_current_metrics(): return {"application": {"requests": {}, "errors": {}, "response_times": {}}}
    def get_recent_alerts(count=10): return []

# Set up loggers
logger = get_app_logger(__name__)
access_logger = get_access_logger()

# Initialize session ID for tracking user sessions
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
    logger.info(f"New session started: {st.session_state['session_id']}")
    
# Start monitoring system
start_monitoring(collection_interval=60)  # Collect metrics every 60 seconds
logger.info("Monitoring system started")

# Set page config
st.set_page_config(
    page_title="CredTech XScore", 
    page_icon="💳", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# CredTech XScore\nAn explainable credit scoring system for financial institutions."
    }
)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state['page'] = 'main'

# Add version info
APP_VERSION = "1.0.0"
BUILD_DATE = "2023-08-20"

# Load model with caching and error handling
@st.cache_resource
@log_function_call()
def load_credit_model():
    try:
        model_path = os.path.join('models', 'model.joblib')
        if not os.path.exists(model_path):
            st.error(f"Model file not found at {model_path}. Please train the model first.")
            logger.error(f"Model file not found at {model_path}")
            return None
        
        logger.info(f"Loading model from {model_path}")
        start_time = time.time()
        model = load_model(model_path)
        load_time = time.time() - start_time
        logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
        
        # Store model version in session state for monitoring
        if hasattr(model, 'version'):
            st.session_state['model_version'] = model.version
        else:
            st.session_state['model_version'] = 'unknown'
            
        return model
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]  # Generate a short error ID for reference
        error_msg = f"Error loading model: {str(e)} (Error ID: {error_id})"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        st.error(f"Error loading model: {str(e)}. Reference ID: {error_id}")
        record_error("model_loading")
        return None

# Enhanced error handling and validation
class EnhancedErrorHandler:
    """Enhanced error handling with detailed logging and user feedback"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, show_to_user: bool = True):
        """Handle errors with comprehensive logging and user feedback"""
        error_id = str(uuid.uuid4())[:8]
        error_type = type(error).__name__
        
        # Log error details
        error_info = {
            'error_id': error_id,
            'error_type': error_type,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        # Update error counts
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Store in history
        self.error_history.append(error_info)
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        # Log to structured logging
        log_structured_error(
            error_type=error_type,
            error_message=str(error),
            source=context.get('source', 'unknown') if context else 'unknown',
            context={
                'error_id': error_id,
                **(context or {})
            },
            stack_trace=traceback.format_exc()
        )
        
        # Show user-friendly error message
        if show_to_user:
            st.error(f"An error occurred (Error ID: {error_id}). Please try again or contact support.")
            
            # Show technical details for admin users
            current_user = get_current_user()
            if current_user and current_user.get('role') == 'admin':
                with st.expander("Technical Details (Admin Only)"):
                    st.code(f"Error Type: {error_type}")
                    st.code(f"Error Message: {str(error)}")
                    st.code(f"Error ID: {error_id}")
                    if context:
                        st.json(context)
        
        return error_id

# Initialize enhanced error handler
error_handler = EnhancedErrorHandler()

# Enhanced performance monitoring
class PerformanceMonitor:
    """Monitor and track performance metrics for the Streamlit app"""
    
    def __init__(self):
        self.page_load_times = {}
        self.component_render_times = {}
        self.start_time = time.time()
    
    def start_page_timer(self, page_name: str):
        """Start timing page load"""
        self.page_load_times[page_name] = time.time()
    
    def end_page_timer(self, page_name: str):
        """End timing page load and record metrics"""
        if page_name in self.page_load_times:
            duration = time.time() - self.page_load_times[page_name]
            
            # Log performance metric
            log_performance_metric(
                metric_name="page_load_time",
                value=duration,
                unit="seconds",
                context={
                    "page": page_name,
                    "session_id": st.session_state.get('session_id', 'unknown')
                }
            )
            
            # Record for monitoring
            if 'page_load_times' not in self.component_render_times:
                self.component_render_times['page_load_times'] = {}
            self.component_render_times['page_load_times'][page_name] = duration
    
    def start_component_timer(self, component_name: str):
        """Start timing component render"""
        return time.time()
    
    def end_component_timer(self, component_name: str, start_time: float):
        """End timing component render and record metrics"""
        duration = time.time() - start_time
        
        # Log performance metric
        log_performance_metric(
            metric_name="component_render_time",
            value=duration,
            unit="seconds",
            context={
                "component": component_name,
                "session_id": st.session_state.get('session_id', 'unknown')
            }
        )
        
        # Record for monitoring
        if component_name not in self.component_render_times:
            self.component_render_times[component_name] = []
        self.component_render_times[component_name].append(duration)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'page_load_times': self.component_render_times.get('page_load_times', {}),
            'component_render_times': {
                k: v for k, v in self.component_render_times.items() 
                if k != 'page_load_times'
            }
        }

# Initialize performance monitor
performance_monitor = PerformanceMonitor()

# Enhanced security decorator
def enhanced_security_check(func):
    """Enhanced security decorator with rate limiting and input validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check rate limiting
        user_id = st.session_state.get('username', 'anonymous')
        if not check_rate_limit(user_id):
            st.error("Rate limit exceeded. Please try again later.")
            st.stop()
        
        # Validate session
        if not validate_session(st.session_state):
            st.error("Invalid session. Please log in again.")
            st.stop()
        
        # Log security check
        log_security_event(
            event_type="security_check_passed",
            user_id=user_id,
            details={
                "function": func.__name__,
                "session_id": st.session_state.get('session_id', 'unknown')
            }
        )
        
        return func(*args, **kwargs)
    return wrapper

def check_rate_limit(user_id: str, max_requests: int = 60) -> bool:
    """Check if user is within rate limits"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Initialize rate limit tracking
    if 'rate_limits' not in st.session_state:
        st.session_state['rate_limits'] = {}
    
    if user_id not in st.session_state['rate_limits']:
        st.session_state['rate_limits'][user_id] = []
    
    # Clean old requests
    st.session_state['rate_limits'][user_id] = [
        timestamp for timestamp in st.session_state['rate_limits'][user_id]
        if timestamp > minute_ago
    ]
    
    # Check limit
    if len(st.session_state['rate_limits'][user_id]) >= max_requests:
        return False
    
    # Add current request
    st.session_state['rate_limits'][user_id].append(current_time)
    return True

def validate_session(session_state: Dict[str, Any]) -> bool:
    """Validate current session"""
    # Check if authenticated
    if not session_state.get('authenticated'):
        return False
    
    # Check session age
    session_start = session_state.get('session_start')
    if session_start:
        try:
            created_time = datetime.fromisoformat(session_start)
            if datetime.now() - created_time > timedelta(hours=24):
                return False
        except ValueError:
            return False
    
    # Check user data
    if not session_state.get('username') or not session_state.get('user_role'):
        return False
    
    return True

# Function to map score to credit rating
@log_function_call()
def map_score_to_rating(score):
    if score >= 0.8:
        return "A", "Very Low Risk", "#008000"  # Green
    elif score >= 0.6:
        return "B", "Low Risk", "#90EE90"  # Light Green
    elif score >= 0.4:
        return "C", "Moderate Risk", "#FFFF00"  # Yellow
    elif score >= 0.2:
        return "D", "High Risk", "#FFA500"  # Orange
    else:
        return "E", "Very High Risk", "#FF0000"  # Red

# Function to create a gauge chart for the score
@log_function_call()
@handle_error
def create_gauge_chart(score):
    fig, ax = plt.subplots(figsize=(4, 3), subplot_kw={'projection': 'polar'})
    
    # Define the gauge
    theta = np.linspace(0, 180, 100) * np.pi / 180
    r = [1] * 100
    
    # Create background
    ax.plot(theta, r, color='lightgray', lw=25, alpha=0.3)
    
    # Create colored segments
    segments = 5
    colors = ['#FF0000', '#FFA500', '#FFFF00', '#90EE90', '#008000']
    labels = ['Very High Risk', 'High Risk', 'Moderate Risk', 'Low Risk', 'Very Low Risk']
    
    for i in range(segments):
        start = i * 180 / segments
        end = (i + 1) * 180 / segments
        segment_theta = np.linspace(start, end, 20) * np.pi / 180
        segment_r = [1] * 20
        ax.plot(segment_theta, segment_r, color=colors[i], lw=25, alpha=0.6)
        
        # Add labels
        mid_theta = (start + end) / 2 * np.pi / 180
        label_r = 1.2
        ha = 'center'
        va = 'center'
        ax.text(mid_theta, label_r, labels[i], ha=ha, va=va, fontsize=8, 
                rotation=mid_theta*180/np.pi - 90, rotation_mode='anchor')
    
    # Add needle
    needle_theta = score * np.pi
    ax.plot([0, needle_theta], [0, 0.8], color='black', lw=2)
    ax.scatter(needle_theta, 0.8, color='black', s=50, zorder=10)
    
    # Add score text in the center
    ax.text(0, 0, f"{score:.2f}", ha='center', va='center', fontsize=14, fontweight='bold')
    
    # Remove unnecessary elements
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylim(0, 1.3)  # Increased to make room for labels
    ax.spines['polar'].set_visible(False)
    
    return fig

# Custom CSS for styling
def load_css():
    # Load external CSS file
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'styles.css')
    
    # Check if file exists
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        logger.error(f"CSS file not found: {css_file}")
        # Fallback to inline styles
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #2563EB;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .metric-container {
            background-color: #F3F4F6;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .rating-card {
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1rem;
        }
        .rating-value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .rating-label {
            font-size: 1.2rem;
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
            color: #6B7280;
            font-size: 0.8rem;
        }
        .sidebar-header {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .explanation-positive {
            color: #10B981;
        }
        .explanation-negative {
            color: #EF4444;
        }
        </style>
        """, unsafe_allow_html=True)

# Main app
# Navigation functions
@handle_error
def show_main_page():
    st.session_state['page'] = 'main'
    log_page_view('main', {'navigation_source': 'button'})

def show_documentation_page():
    st.session_state['page'] = 'documentation'
    log_page_view('documentation', {'navigation_source': 'button'})

@handle_error
def show_settings_page():
    st.session_state['page'] = 'settings'
    log_page_view('settings', {'navigation_source': 'button'})
    
@handle_error
def show_monitoring_page():
    st.session_state['page'] = 'monitoring'
    log_page_view('monitoring', {'navigation_source': 'button'})
    
def show_user_management_page():
    st.session_state['page'] = 'user_management'
    log_page_view('user_management', {'navigation_source': 'button'})
    
def show_log_viewer_page():
    st.session_state['page'] = 'log_viewer'
    log_page_view('log_viewer', {'navigation_source': 'button'})

# Main application function
@require_auth
@log_user_action("dashboard_access")
@enhanced_security_check
def main():
    # Start performance monitoring
    performance_monitor.start_page_timer('main')
    
    try:
        # Load custom CSS
        load_css()
        
        # Log user access
        current_user = get_current_user()
        access_logger.info(
            f"Dashboard accessed by {current_user['full_name']}",
            extra={
                'extra': {
                    'user': current_user['username'],
                    'role': current_user['role'],
                    'session_id': st.session_state['session_id']
                }
            }
        )
        
        # Navigation bar with performance monitoring
        with performance_monitor.start_component_timer("navigation_bar"):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            with col1:
                st.markdown('<h1 class="main-header">CredTech XScore</h1>', unsafe_allow_html=True)
            with col2:
                if st.button("Dashboard", key="nav_main"):
                    log_button_click("nav_main", {"destination": "main"})
                    show_main_page()
            with col3:
                if st.button("Documentation", key="nav_docs"):
                    log_button_click("nav_docs", {"destination": "documentation"})
                    show_documentation_page()
        with col4:
            if st.button("Monitoring", key="nav_monitoring"):
                log_button_click("nav_monitoring", {"destination": "monitoring"})
                show_monitoring_page()
        with col5:
            if st.button("Settings", key="nav_settings"):
                log_button_click("nav_settings", {"destination": "settings"})
                show_settings_page()
        with col6:
            # Only show user management button for admin users
            current_role = current_user.get('role', '')
            if current_role == 'admin':
                if st.button("Users", key="nav_users"):
                    log_button_click("nav_users", {"destination": "user_management", "user_role": current_role})
                    show_user_management_page()
    
            # User info and logout in sidebar
            with st.sidebar:
                st.markdown(f"**Logged in as:** {current_user['full_name']} ({current_user['role']})")
        
                # Admin tools section
                if current_user.get('role') == 'admin':
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("**Admin Tools**")
                    if st.sidebar.button("Log Viewer", key="nav_log_viewer"):
                        log_button_click("nav_log_viewer", {"destination": "log_viewer", "user_role": current_user['role']})
                        show_log_viewer_page()
                    
                    # Performance monitoring for admins
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("**Performance Monitor**")
                    if st.sidebar.button("View Metrics", key="view_metrics"):
                        show_performance_metrics()
                    
                    # System optimization for admins
                    if st.sidebar.button("Optimize System", key="optimize_system"):
                        optimize_system_resources()
                
                if st.button("Logout"):
                    log_button_click("logout", {"user": current_user['username'], "role": current_user['role']})
                    logout_user()
                    st.experimental_rerun()
    
            # App header
            st.markdown('<p style="text-align: center;">Explainable Credit Scoring System</p>', unsafe_allow_html=True)
            
            # Load model with enhanced error handling
            with st.spinner("Loading credit scoring model..."):
                model = load_credit_model()
                
            if model is None:
                st.warning("Please run the training pipeline first to generate a model.")
                st.info("Run `python run_all.py` to generate the model.")
                return
    
        # Sidebar for input parameters with performance monitoring
        with performance_monitor.start_component_timer("sidebar_parameters"):
            st.sidebar.markdown('<div class="sidebar-header">Input Parameters</div>', unsafe_allow_html=True)
            
            # Add tabs for different input methods
            input_method = st.sidebar.radio(
                "Select Input Method",
                ["Manual Entry", "Sample Profiles"]
            )
            log_input_change("input_method", input_method, {"available_options": ["Manual Entry", "Sample Profiles"]})
            
            # Initialize profile variable
            profile = None
            
            if input_method == "Sample Profiles":
                profile = st.sidebar.selectbox(
                    "Select a sample profile",
                    ["High Income Professional", "Average Consumer", "Student", "Small Business Owner"]
                )
                log_selectbox_change("profile", profile, {
                    "available_options": ["High Income Professional", "Average Consumer", "Student", "Small Business Owner"]
                })
                
                # Pre-defined profiles with enhanced validation
                profile_data = get_sample_profile_data(profile)
                if profile_data:
                    display_profile_inputs(profile_data)
                else:
                    st.error("Invalid profile selected")
                    return
            else:
                # Manual entry with enhanced validation
                display_manual_inputs()
        
        # Main content area with performance monitoring
        with performance_monitor.start_component_timer("main_content"):
            # Display model information
            display_model_info(model)
            
            # Display credit score prediction
            if st.button("Calculate Credit Score", key="calculate_score"):
                calculate_and_display_score(model)
            
            # Display recent predictions
            display_recent_predictions()
        
        # End performance monitoring
        performance_monitor.end_page_timer('main')
        
    except Exception as e:
        # Enhanced error handling
        error_context = {
            'source': 'main_page',
            'user': current_user.get('username', 'unknown'),
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        error_handler.handle_error(e, error_context)
        
        # End performance monitoring even on error
        performance_monitor.end_page_timer('main')

def get_sample_profile_data(profile: str) -> Optional[Dict[str, Any]]:
    """Get sample profile data with validation"""
    profiles = {
        "High Income Professional": {
            "issuer": "ABC",
            "income": 150000,
            "balance": 25000,
            "transactions": 25,
            "news_sentiment": 0.6
        },
        "Average Consumer": {
            "issuer": "XYZ",
            "income": 75000,
            "balance": 12000,
            "transactions": 15,
            "news_sentiment": 0.2
        },
        "Student": {
            "issuer": "LMN",
            "income": 35000,
            "balance": 5000,
            "transactions": 8,
            "news_sentiment": 0.0
        },
        "Small Business Owner": {
            "issuer": "QRS",
            "income": 120000,
            "balance": 30000,
            "transactions": 35,
            "news_sentiment": 0.4
        }
    }
    
    return profiles.get(profile)

def display_profile_inputs(profile_data: Dict[str, Any]):
    """Display inputs for selected profile"""
    st.sidebar.markdown("**Profile Data:**")
    for key, value in profile_data.items():
        st.sidebar.text_input(key.replace('_', ' ').title(), value, key=f"profile_{key}")

def display_manual_inputs():
    """Display manual input fields with validation"""
    st.sidebar.markdown("**Manual Entry:**")
    
    # Input fields with validation
    issuer = st.sidebar.text_input("Issuer Code", "ABC", key="manual_issuer")
    income = st.sidebar.number_input("Annual Income ($)", min_value=0, value=75000, key="manual_income")
    balance = st.sidebar.number_input("Account Balance ($)", min_value=0, value=12000, key="manual_balance")
    transactions = st.sidebar.number_input("Monthly Transactions", min_value=0, value=15, key="manual_transactions")
    news_sentiment = st.sidebar.slider("News Sentiment", -1.0, 1.0, 0.0, 0.1, key="manual_sentiment")
    
    # Store in session state
    st.session_state['manual_inputs'] = {
        'issuer': issuer,
        'income': income,
        'balance': balance,
        'transactions': transactions,
        'news_sentiment': news_sentiment
    }

def display_model_info(model):
    """Display model information"""
    st.markdown("## Model Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Model Version", getattr(model, 'version', 'Unknown'))
        st.metric("Model Type", getattr(model, 'model_type', 'LightGBM'))
    
    with col2:
        st.metric("Training Date", getattr(model, 'training_date', 'Unknown'))
        st.metric("Features", getattr(model, 'n_features', 'Unknown'))

def calculate_and_display_score(model):
    """Calculate and display credit score with enhanced error handling"""
    try:
        # Get input data
        if 'manual_inputs' in st.session_state:
            inputs = st.session_state['manual_inputs']
        else:
            st.error("Please provide input parameters")
            return
        
        # Validate inputs
        validation_result = validate_inputs(inputs)
        if not validation_result['valid']:
            st.error("Input validation failed:")
            for error in validation_result['errors']:
                st.warning(error)
            return
        
        # Make prediction with performance monitoring
        start_time = time.time()
        prediction = model.predict_proba([list(inputs.values())])[0]
        prediction_time = time.time() - start_time
        
        # Log prediction
        log_model_prediction(
            model_version=getattr(model, 'version', 'unknown'),
            input_features=inputs,
            prediction=prediction.tolist(),
            prediction_time=prediction_time
        )
        
        # Display results
        display_prediction_results(prediction, inputs, prediction_time)
        
    except Exception as e:
        error_context = {
            'source': 'score_calculation',
            'inputs': inputs if 'inputs' in locals() else None
        }
        error_handler.handle_error(e, error_context)

def validate_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input parameters"""
    errors = []
    
    if not inputs.get('issuer') or len(inputs['issuer']) < 2:
        errors.append("Issuer code must be at least 2 characters")
    
    if inputs.get('income', 0) <= 0:
        errors.append("Income must be positive")
    
    if inputs.get('balance', 0) < 0:
        errors.append("Balance cannot be negative")
    
    if inputs.get('transactions', 0) < 0:
        errors.append("Transaction count cannot be negative")
    
    if not -1 <= inputs.get('news_sentiment', 0) <= 1:
        errors.append("News sentiment must be between -1 and 1")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def display_prediction_results(prediction, inputs, prediction_time):
    """Display prediction results with enhanced visualization"""
    st.markdown("## Credit Score Prediction Results")
    
    # Calculate score and rating
    score = prediction[1] * 1000  # Convert probability to 0-1000 scale
    rating = get_credit_rating(score)
    
    # Display score and rating
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Credit Score", f"{score:.0f}", delta=None)
    
    with col2:
        st.metric("Risk Rating", rating, delta=None)
    
    with col3:
        st.metric("Prediction Time", f"{prediction_time:.3f}s", delta=None)
    
    # Display detailed breakdown
    st.markdown("### Score Breakdown")
    
    # Create a more detailed visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Bar chart of input factors
    factors = list(inputs.keys())
    values = list(inputs.values())
    
    # Normalize values for visualization
    normalized_values = [(v - min(values)) / (max(values) - min(values)) if max(values) != min(values) else 0.5 for v in values]
    
    bars = ax.bar(factors, normalized_values)
    ax.set_title("Input Factor Contributions")
    ax.set_ylabel("Normalized Value")
    
    # Color bars based on impact
    for i, (bar, value) in enumerate(zip(bars, values)):
        if value > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Store prediction in session state for history
    if 'prediction_history' not in st.session_state:
        st.session_state['prediction_history'] = []
    
    st.session_state['prediction_history'].append({
        'timestamp': datetime.now().isoformat(),
        'inputs': inputs,
        'score': score,
        'rating': rating,
        'prediction_time': prediction_time
    })

def get_credit_rating(score: float) -> str:
    """Get credit rating based on score"""
    if score >= 800:
        return "A (Excellent)"
    elif score >= 700:
        return "B (Good)"
    elif score >= 600:
        return "C (Fair)"
    elif score >= 500:
        return "D (Poor)"
    else:
        return "E (Very Poor)"

def display_recent_predictions():
    """Display recent prediction history"""
    if 'prediction_history' in st.session_state and st.session_state['prediction_history']:
        st.markdown("## Recent Predictions")
        
        # Show last 5 predictions
        recent = st.session_state['prediction_history'][-5:]
        
        for i, pred in enumerate(reversed(recent)):
            with st.expander(f"Prediction {len(recent) - i} - {pred['timestamp'][:19]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Score:** {pred['score']:.0f}")
                    st.write(f"**Rating:** {pred['rating']}")
                with col2:
                    st.write(f"**Time:** {pred['prediction_time']:.3f}s")
                
                # Show inputs
                st.write("**Inputs:**")
                for key, value in pred['inputs'].items():
                    st.write(f"- {key.replace('_', ' ').title()}: {value}")

def show_performance_metrics():
    """Show performance metrics for admin users"""
    st.markdown("## Performance Metrics")
    
    # Get performance summary
    summary = performance_monitor.get_performance_summary()
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Uptime", f"{summary['uptime_seconds']:.0f}s")
        
        if 'page_load_times' in summary:
            avg_page_time = sum(summary['page_load_times'].values()) / len(summary['page_load_times']) if summary['page_load_times'] else 0
            st.metric("Avg Page Load Time", f"{avg_page_time:.3f}s")
    
    with col2:
        st.metric("Total Components Monitored", len(summary.get('component_render_times', {})))
        
        if 'component_render_times' in summary:
            total_renders = sum(len(times) for times in summary['component_render_times'].values())
            st.metric("Total Component Renders", total_renders)
    
    # Show detailed metrics
    if 'component_render_times' in summary:
        st.markdown("### Component Performance")
        
        for component, times in summary['component_render_times'].items():
            if times:
                avg_time = sum(times) / len(times)
                st.write(f"**{component}:** {avg_time:.3f}s avg ({len(times)} renders)")

def optimize_system_resources():
    """Optimize system resources for admin users"""
    st.markdown("## System Optimization")
    
    try:
        # Import performance utilities
        from src.utils.performance import optimize_system, get_memory_usage, get_cpu_usage
        
        # Get current system status
        memory_info = get_memory_usage()
        cpu_usage = get_cpu_usage()
        
        st.write(f"**Current Memory Usage:** {memory_info['percent']:.1f}%")
        st.write(f"**Current CPU Usage:** {cpu_usage:.1f}%")
        
        if st.button("Run Optimization"):
            with st.spinner("Optimizing system resources..."):
                optimization_result = optimize_system()
                
                st.success("System optimization completed!")
                st.write(f"**Garbage Collected:** {optimization_result['garbage_collected']} objects")
                st.write(f"**Memory Usage:** {optimization_result['memory_usage_percent']:.1f}%")
                
                # Refresh metrics
                st.experimental_rerun()
    
    except ImportError:
        st.error("Performance optimization module not available")
    except Exception as e:
        error_context = {'source': 'system_optimization'}
        error_handler.handle_error(e, error_context)

# Documentation page
def documentation_page():
    st.markdown('<h1 class="main-header">Documentation</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## CredTech XScore User Guide
    
    ### Overview
    CredTech XScore is an explainable credit scoring system designed to help financial institutions make more transparent and fair lending decisions.
    
    ### Features
    - **Credit Score Generation**: Generate credit scores based on financial and behavioral data
    - **Explainability**: Understand the factors that influence each score
    - **Customizable Inputs**: Adjust parameters to see how they affect the credit score
    - **Visual Dashboard**: Intuitive visualization of credit scores and risk factors
    
    ### How to Use
    1. Select input method (Manual Entry or Sample Profiles)
    2. Enter or select financial parameters
    3. View the generated credit score and explanation
    4. Explore different tabs for detailed information
    
    ### Understanding the Score
    - **Credit Score**: A number between 0 and 1, with higher values indicating lower risk
    - **Credit Rating**: A letter grade from A to F based on the credit score
    - **Risk Assessment**: A qualitative assessment of the credit risk
    - **Positive/Negative Factors**: The main factors that contribute to or detract from the score
    
    ### Technical Details
    The credit score is generated using a machine learning model trained on historical data. The model uses the following features:
    - Issuer information
    - Income level
    - Current balance
    - Transaction history
    - News sentiment
    
    For more information, please contact support@credtech.com
    """)
    
    # Version information
    st.markdown("---")
    st.markdown(f"**Version:** {APP_VERSION}")
    st.markdown(f"**Build Date:** {BUILD_DATE}")

# Settings page
@handle_error
def settings_page():
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)
    
    # Get current user
    current_user = get_current_user()
    
    # Only show user management for admins
    if current_user and current_user.get("role") == "admin":
        from src.utils.streamlit_auth import display_user_management
        display_user_management()
    
    # Theme settings
    st.markdown("## Theme Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"], index=0)
    
    # Notification settings
    st.markdown("## Notification Settings")
    email_notifications = st.checkbox("Email Notifications", value=False)
    
    # Save settings button
    if st.button("Save Settings"):
        try:
            # Validate email if notifications are enabled
            if email_notifications and current_user.get("email"):
                email_validation = validate_email(current_user.get("email"))
                if not email_validation.is_valid:
                    raise ValidationError("Invalid email address for notifications", 
                                         details={"errors": email_validation.errors})
            
            # Save settings (sanitized)
            settings_data = sanitize_dict({
                "theme": theme,
                "email_notifications": email_notifications
            })
            
            # Success message
            st.success("Settings saved successfully!")
        except Exception as e:
            handle_error("save_settings", e)

# Monitoring page function
def monitoring_page():
    st.title("System Monitoring")
    
    try:
        # Try to import psutil to check if it's available
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False
        st.warning("The psutil package is not installed. Some system metrics may not be available. Install it with 'pip install psutil' for full monitoring capabilities.")
    
    try:
        # Get current metrics and recent alerts
        metrics = get_current_metrics()
        alerts = get_recent_alerts(10)  # Get last 10 alerts
        
        # Create tabs for different metric categories
        system_tab, app_tab, alerts_tab = st.tabs(["System Metrics", "Application Metrics", "Recent Alerts"])
        
        with system_tab:
            st.subheader("System Health")
            
            if psutil_available and "system" in metrics:
                # Create columns for system metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("CPU Usage", f"{metrics['system']['cpu']['usage_percent']:.1f}%")
                    
                with col2:
                    st.metric("Memory Usage", f"{metrics['system']['memory']['percent']:.1f}%")
                    
                with col3:
                    st.metric("Disk Usage", f"{metrics['system']['disk']['percent']:.1f}%")
                
                # Show detailed system info
                st.subheader("Detailed System Information")
                st.json(metrics["system"])
            else:
                st.info("System metrics are not available. Install psutil package for system monitoring.")
        
        with app_tab:
            st.subheader("Application Metrics")
            
            if "application" in metrics:
                # Create columns for key application metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Active Users", metrics["application"].get("users", {}).get("active", 0))
                    
                with col2:
                    st.metric("Total Requests", metrics["application"]["requests"].get("total", 0))
                    
                with col3:
                    st.metric("Total Errors", metrics["application"]["errors"].get("total", 0))
                
                # Show request rates by endpoint
                st.subheader("Request Rates by Endpoint")
                request_rates = metrics["application"]["requests"].get("rates", {})
                if request_rates:
                    st.bar_chart(pd.DataFrame(list(request_rates.items()), columns=["Endpoint", "Requests"]).set_index("Endpoint"))
                else:
                    st.info("No request data available yet")
                
                # Show response times
                st.subheader("Average Response Times")
                response_times = metrics["application"]["response_times"].get("average", {})
                if response_times:
                    st.bar_chart(pd.DataFrame(list(response_times.items()), columns=["Endpoint", "Time (s)"]).set_index("Endpoint"))
                else:
                    st.info("No response time data available yet")
                
                # Show prediction metrics if available
                if "predictions" in metrics["application"]:
                    st.subheader("Model Predictions")
                    prediction_counts = metrics["application"]["predictions"].get("by_model", {})
                    if prediction_counts:
                        st.bar_chart(pd.DataFrame(list(prediction_counts.items()), columns=["Model", "Count"]).set_index("Model"))
                    
                    # Show prediction latencies
                    st.subheader("Prediction Latencies")
                    prediction_latencies = metrics["application"]["predictions"].get("latencies", {})
                    if prediction_latencies:
                        st.bar_chart(pd.DataFrame(list(prediction_latencies.items()), columns=["Model", "Latency (s)"]).set_index("Model"))
            else:
                st.info("Application metrics are not available yet. Use the application to generate metrics.")
        
        with alerts_tab:
            st.subheader("Recent Alerts")
            
            if not alerts:
                st.success("No recent alerts - all systems operating normally")
            else:
                for alert in alerts:
                    with st.expander(f"{alert['type']} - {alert['timestamp']}"):
                        st.write(f"**Message:** {alert['data'].get('message', 'No message provided')}")
                        st.write(f"**Current Value:** {alert['data'].get('current', 'N/A')}")
                        st.write(f"**Threshold:** {alert['data'].get('threshold', 'N/A')}")
                        st.json(alert['data'])
    except Exception as e:
        st.error(f"Error loading monitoring data: {str(e)}")
        st.info("Make sure the monitoring system is properly initialized and all required packages are installed.")
        import traceback
        st.code(traceback.format_exc())

# User Management Page
@require_auth
@log_user_action("user_management_access")
@handle_error
def user_management_page():
    st.title("User Management")
    
    # Check if user is admin
    current_user = get_current_user()
    if current_user.get('role') != 'admin':
        raise AuthenticationError("You do not have permission to access this page.")
    
    # Get all users
    users_data = get_users_data()
    
    # Import necessary functions
    from src.utils.streamlit_auth import create_user, update_user, change_password, delete_user
    
    # Create tabs for different user management functions
    user_list_tab, create_user_tab, edit_user_tab = st.tabs(["User List", "Create User", "Edit User"])
    
    with user_list_tab:
        st.subheader("Current Users")
        
        # Convert users to a list for display
        users_list = []
        for username, user_info in users_data.items():
            users_list.append({
                "Username": username,
                "Full Name": user_info.get("full_name", ""),
                "Email": user_info.get("email", ""),
                "Role": user_info.get("role", "user"),
                "Last Login": user_info.get("last_login", "Never")
            })
        
        if users_list:
            users_df = pd.DataFrame(users_list)
            st.dataframe(users_df)
            
            # Delete user section
            st.subheader("Delete User")
            delete_cols = st.columns([3, 1])
            with delete_cols[0]:
                username_to_delete = st.selectbox("Select user to delete", 
                                                options=[user["Username"] for user in users_list],
                                                key="username_to_delete")
            with delete_cols[1]:
                if st.button("Delete User", key="delete_user_btn"):
                    if username_to_delete == current_user["username"]:
                        raise ValidationError("You cannot delete your own account.")
                    else:
                        if delete_user(username_to_delete):
                            st.success(f"User '{username_to_delete}' deleted successfully.")
                            st.experimental_rerun()
                        else:
                            raise ValidationError("Cannot delete the last admin user.")
        else:
            st.info("No users found.")
    
    with create_user_tab:
        st.subheader("Create New User")
        with st.form("create_user_form"):
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")
            new_full_name = st.text_input("Full Name", key="new_full_name")
            new_email = st.text_input("Email", key="new_email")
            new_role = st.selectbox("Role", options=["user", "admin"], key="new_role")
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                # Validate inputs using validation utilities
                validation_results = []
                validation_results.append(validate_not_empty(new_username, "Username"))
                validation_results.append(validate_password_strength(new_password))
                
                if new_email:
                    validation_results.append(validate_email(new_email))
                
                # Check for existing username
                if new_username in users_data:
                    validation_results.append(ValidationResult(False, [f"User '{new_username}' already exists."]))
                
                # Collect all errors
                errors = []
                for result in validation_results:
                    if not result.is_valid:
                        errors.extend(result.errors)
                
                if errors:
                    raise ValidationError("Please fix the following errors:", details={"errors": errors})
                else:
                    # Sanitize inputs
                    safe_username = sanitize_input(new_username)
                    safe_full_name = sanitize_input(new_full_name)
                    safe_email = sanitize_input(new_email)
                    
                    # Create new user
                    create_user(safe_username, new_password, safe_full_name, safe_email, new_role)
                    st.success(f"User '{safe_username}' created successfully.")
                    st.experimental_rerun()
    
    with edit_user_tab:
        st.subheader("Edit User")
        
        # Select user to edit
        username_to_edit = st.selectbox("Select user to edit", 
                                      options=[user["Username"] for user in users_list],
                                      key="username_to_edit")
        
        if username_to_edit:
            user_info = users_data[username_to_edit]
            
            # Create tabs for editing different aspects of the user
            profile_tab, password_tab = st.tabs(["Profile Information", "Change Password"])
            
            with profile_tab:
                with st.form("edit_user_form"):
                    edit_full_name = st.text_input("Full Name", 
                                                value=user_info.get("full_name", ""),
                                                key="edit_full_name")
                    edit_email = st.text_input("Email", 
                                            value=user_info.get("email", ""),
                                            key="edit_email")
                    edit_role = st.selectbox("Role", 
                                           options=["user", "admin"],
                                           index=0 if user_info.get("role") == "user" else 1,
                                           key="edit_role")
                    
                    update_button = st.form_submit_button("Update User")
                    
                    if update_button:
                        # Validate inputs
                        validation_results = []
                        
                        if edit_email:
                            validation_results.append(validate_email(edit_email))
                        
                        # Check if this is the last admin and trying to change role
                        if user_info.get("role") == "admin" and edit_role != "admin":
                            admin_count = sum(1 for user in users_data.values() if user.get("role") == "admin")
                            if admin_count <= 1:
                                validation_results.append(ValidationResult(False, ["Cannot change role of the last admin user."]))
                        
                        # Collect all errors
                        errors = []
                        for result in validation_results:
                            if not result.is_valid:
                                errors.extend(result.errors)
                        
                        if errors:
                            raise ValidationError("Please fix the following errors:", details={"errors": errors})
                        else:
                            # Sanitize inputs
                            safe_full_name = sanitize_input(edit_full_name)
                            safe_email = sanitize_input(edit_email)
                            
                            # Update user
                            update_user(username_to_edit, safe_full_name, safe_email, edit_role)
                            st.success(f"User '{username_to_edit}' updated successfully.")
                            st.experimental_rerun()
            
            with password_tab:
                with st.form("change_password_form"):
                    new_password = st.text_input("New Password", type="password", key="change_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                    
                    password_button = st.form_submit_button("Change Password")
                    
                    if password_button:
                        validation_results = []
                        
                        # Validate password
                        if not new_password:
                            validation_results.append(ValidationResult(False, ["Password cannot be empty."]))
                        else:
                            validation_results.append(validate_password_strength(new_password))
                        
                        # Check if passwords match
                        if new_password != confirm_password:
                            validation_results.append(ValidationResult(False, ["Passwords do not match."]))
                        
                        # Collect all errors
                        errors = []
                        for result in validation_results:
                            if not result.is_valid:
                                errors.extend(result.errors)
                        
                        if errors:
                            raise ValidationError("Please fix the following errors:", details={"errors": errors})
                        else:
                            # Change password
                            change_password(username_to_edit, new_password)
                            st.success(f"Password for user '{username_to_edit}' changed successfully.")
                            st.experimental_rerun()

# Router function to handle page navigation
@handle_error
def router():
    # Check if user is authenticated
    if not is_authenticated():
        display_login_form()
        return
    
    # Get current page and log page view
    current_page = st.session_state.get('page', 'main')
    log_page_view(current_page)
    
    # Log structured security event for page access
    current_user = get_current_user()
    log_structured_security_event(
        event_type="page_access",
        user_id=current_user.get('username', 'anonymous') if current_user else 'anonymous',
        details={
            "page": current_page,
            "user_role": current_user.get('role', 'none') if current_user else 'none',
            "session_id": st.session_state.get('session_id', 'unknown')
        }
    )
    
    # Route to the appropriate page
    try:
        if current_page == 'main':
            main()
        elif current_page == 'documentation':
            documentation_page()
        elif current_page == 'settings':
            settings_page()
        elif current_page == 'monitoring':
            monitoring_page()
        elif current_page == 'user_management':
            user_management_page()
        elif current_page == 'log_viewer':
            from src.serve.log_viewer import log_viewer_page
            log_viewer_page()
        else:
            log_with_context(get_app_logger(), "error", f"Unknown page requested: {current_page}")
            raise ValidationError(f"Unknown page: {current_page}")
    except Exception as e:
        # Log the error with context
        context = get_session_context()
        context['error'] = str(e)
        context['traceback'] = traceback.format_exc()
        log_with_context(get_app_logger(), "error", f"Error in router: {str(e)}", context)
        
        # Log structured error
        log_structured_error(
            error_type="router_error",
            error_message=str(e),
            source="router",
            context={
                "page": current_page,
                "user": st.session_state.get('username', 'anonymous'),
                "session_id": st.session_state.get('session_id', 'unknown')
            },
            stack_trace=traceback.format_exc()
        )
        
        # Display error message
        st.error("An error occurred while loading the page. Please try again or contact support.")
        
        # Show technical details to admin users
        current_user = get_current_user()
        if current_user and current_user.get('role') == 'admin':
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())
        
        # Redirect to main page
        st.session_state['page'] = 'main'
        log_page_view('main', {'redirect_reason': 'error', 'original_page': current_page})
        main()

# Function to handle form submissions with validation
def handle_form_submission(form_data, validation_rules, on_success):
    """Handle form submission with validation
    
    Args:
        form_data: Dictionary of form field values
        validation_rules: Dictionary mapping field names to validation functions
        on_success: Callback function to execute if validation passes
    
    Returns:
        bool: True if validation passed, False otherwise
    """
    errors = []
    
    # Apply validation rules
    for field, validator in validation_rules.items():
        if field in form_data:
            result = validator(form_data[field])
            if not result.is_valid:
                errors.extend(result.errors)
    
    # Handle validation results
    if errors:
        st.error("Please fix the following errors:")
        for error in errors:
            st.warning(error)
        return False
    else:
        # Sanitize inputs before passing to callback
        sanitized_data = {k: sanitize_input(v) if isinstance(v, str) else v 
                         for k, v in form_data.items()}
        on_success(sanitized_data)
        return True

# Entry point
if __name__ == "__main__":
    # Initialize monitoring system if available
    if monitoring_available:
        try:
            # Start monitoring system to collect metrics every 60 seconds
            start_monitoring(collection_interval=60)
            print("Monitoring system started successfully")
        except Exception as e:
            print(f"Error starting monitoring system: {e}")
    
    try:
        router()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"An unexpected error occurred: {str(e)}")
        
        # Show technical details for admins
        if is_authenticated() and get_current_user().get("role") == "admin":
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())

# Function to map score to risk level for monitoring purposes
@log_function_call()
def map_score_to_risk(score):
    if score >= 0.8:
        return "very_low"
    elif score >= 0.6:
        return "low"
    elif score >= 0.4:
        return "moderate"
    elif score >= 0.2:
        return "high"
    else:
        return "very_high"

# Decorator to track prediction metrics
def track_prediction(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        prediction_time = time.time() - start_time
        
        # Record prediction metrics if successful
        if result is not None:
            model_version = st.session_state.get('model_version', 'unknown')
            record_prediction(model_version, prediction_time)
            
        return result
    return wrapper