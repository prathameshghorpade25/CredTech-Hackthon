"""Configuration file for CredTech XScore Dashboard"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class DashboardConfig:
    """Main dashboard configuration"""
    
    # Application settings
    app_name: str = "CredTech XScore"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    
    # Security settings
    enable_authentication: bool = True
    session_timeout_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_cache_size: int = 1000
    enable_performance_monitoring: bool = True
    performance_metrics_interval: int = 60
    
    # Logging settings
    log_level: str = "INFO"
    enable_structured_logging: bool = True
    enable_file_logging: bool = True
    log_rotation_max_size_mb: int = 10
    log_rotation_backup_count: int = 10
    
    # Monitoring settings
    enable_monitoring: bool = True
    monitoring_interval_seconds: int = 60
    enable_alerting: bool = True
    alert_thresholds: Dict[str, float] = None
    
    # UI/UX settings
    theme: str = "light"
    enable_responsive_design: bool = True
    enable_animations: bool = True
    page_title: str = "CredTech XScore - Explainable Credit Scoring"
    
    # Data settings
    max_data_points: int = 10000
    enable_data_validation: bool = True
    enable_input_sanitization: bool = True
    
    def __post_init__(self):
        """Set default values after initialization"""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_usage_percent': 80.0,
                'memory_usage_percent': 85.0,
                'disk_usage_percent': 90.0,
                'response_time_ms': 5000,
                'error_rate_percent': 5.0
            }

@dataclass
class SecurityConfig:
    """Security configuration"""
    
    # Authentication
    jwt_secret_key: str = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Password policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    
    # Session security
    enable_session_tracking: bool = True
    enable_ip_validation: bool = True
    enable_user_agent_validation: bool = True
    
    # Rate limiting
    enable_rate_limiting: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 60
    
    def __post_init__(self):
        """Generate JWT secret if not provided"""
        if self.jwt_secret_key is None:
            import secrets
            self.jwt_secret_key = secrets.token_urlsafe(64)

@dataclass
class PerformanceConfig:
    """Performance configuration"""
    
    # Caching
    enable_lru_cache: bool = True
    lru_cache_max_size: int = 1000
    enable_memory_cache: bool = True
    memory_cache_ttl: int = 300
    
    # Database optimization
    enable_connection_pooling: bool = True
    max_database_connections: int = 20
    connection_timeout_seconds: int = 30
    
    # Async processing
    enable_async_processing: bool = True
    max_worker_threads: int = 4
    task_queue_size: int = 100
    
    # Memory management
    enable_garbage_collection: bool = True
    gc_interval_seconds: int = 300
    memory_cleanup_threshold_percent: float = 85.0

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    
    # Metrics collection
    enable_metrics_collection: bool = True
    metrics_collection_interval: int = 60
    enable_prometheus_export: bool = True
    prometheus_port: int = 8000
    
    # Logging
    enable_access_logging: bool = True
    enable_error_logging: bool = True
    enable_performance_logging: bool = True
    enable_security_logging: bool = True
    
    # Alerting
    enable_email_alerts: bool = False
    enable_slack_alerts: bool = False
    alert_email_recipients: List[str] = None
    slack_webhook_url: str = None
    
    # Health checks
    enable_health_checks: bool = True
    health_check_interval: int = 30
    health_check_timeout: int = 10

@dataclass
class UIConfig:
    """UI/UX configuration"""
    
    # Theme and styling
    primary_color: str = "#2563EB"
    secondary_color: str = "#10B981"
    accent_color: str = "#F59E0B"
    error_color: str = "#EF4444"
    warning_color: str = "#F59E0B"
    success_color: str = "#10B981"
    
    # Layout
    sidebar_width: str = "300px"
    main_content_width: str = "auto"
    enable_sidebar_collapse: bool = True
    
    # Components
    enable_charts: bool = True
    enable_tables: bool = True
    enable_forms: bool = True
    enable_modals: bool = True
    
    # Responsiveness
    enable_mobile_optimization: bool = True
    breakpoint_small: int = 768
    breakpoint_medium: int = 1024
    breakpoint_large: int = 1200

@dataclass
class DataConfig:
    """Data handling configuration"""
    
    # Validation
    enable_input_validation: bool = True
    enable_output_validation: bool = True
    max_input_length: int = 1000
    max_file_size_mb: int = 10
    
    # Sanitization
    enable_input_sanitization: bool = True
    enable_output_sanitization: bool = True
    allowed_html_tags: List[str] = None
    blocked_patterns: List[str] = None
    
    # Storage
    enable_data_persistence: bool = True
    data_storage_path: str = "data/dashboard"
    max_storage_size_gb: int = 10
    
    # Caching
    enable_data_caching: bool = True
    cache_expiration_hours: int = 24
    max_cached_items: int = 1000

# Create default configuration instances
dashboard_config = DashboardConfig()
security_config = SecurityConfig()
performance_config = PerformanceConfig()
monitoring_config = MonitoringConfig()
ui_config = UIConfig()
data_config = DataConfig()

# Environment variable overrides
def load_config_from_env():
    """Load configuration from environment variables"""
    global dashboard_config, security_config, performance_config, monitoring_config, ui_config, data_config
    
    # Dashboard config
    if os.getenv('DASHBOARD_DEBUG_MODE'):
        dashboard_config.debug_mode = os.getenv('DASHBOARD_DEBUG_MODE').lower() == 'true'
    
    if os.getenv('DASHBOARD_LOG_LEVEL'):
        dashboard_config.log_level = os.getenv('DASHBOARD_LOG_LEVEL')
    
    # Security config
    if os.getenv('SECURITY_JWT_SECRET'):
        security_config.jwt_secret_key = os.getenv('SECURITY_JWT_SECRET')
    
    if os.getenv('SECURITY_SESSION_TIMEOUT'):
        dashboard_config.session_timeout_hours = int(os.getenv('SECURITY_SESSION_TIMEOUT'))
    
    # Performance config
    if os.getenv('PERFORMANCE_CACHE_TTL'):
        performance_config.memory_cache_ttl = int(os.getenv('PERFORMANCE_CACHE_TTL'))
    
    # Monitoring config
    if os.getenv('MONITORING_PROMETHEUS_PORT'):
        monitoring_config.prometheus_port = int(os.getenv('MONITORING_PROMETHEUS_PORT'))
    
    # UI config
    if os.getenv('UI_THEME'):
        ui_config.theme = os.getenv('UI_THEME')

# Load configuration on import
load_config_from_env()

# Configuration validation
def validate_config() -> List[str]:
    """Validate configuration and return any errors"""
    errors = []
    
    # Dashboard config validation
    if dashboard_config.session_timeout_hours <= 0:
        errors.append("Session timeout must be positive")
    
    if dashboard_config.max_requests_per_minute <= 0:
        errors.append("Max requests per minute must be positive")
    
    # Security config validation
    if security_config.min_password_length < 6:
        errors.append("Minimum password length must be at least 6 characters")
    
    if security_config.rate_limit_max_requests <= 0:
        errors.append("Rate limit max requests must be positive")
    
    # Performance config validation
    if performance_config.lru_cache_max_size <= 0:
        errors.append("LRU cache max size must be positive")
    
    if performance_config.max_database_connections <= 0:
        errors.append("Max database connections must be positive")
    
    # Monitoring config validation
    if monitoring_config.metrics_collection_interval <= 0:
        errors.append("Metrics collection interval must be positive")
    
    if monitoring_config.prometheus_port <= 0 or monitoring_config.prometheus_port > 65535:
        errors.append("Prometheus port must be between 1 and 65535")
    
    return errors

# Configuration getters
def get_dashboard_config() -> DashboardConfig:
    """Get dashboard configuration"""
    return dashboard_config

def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return security_config

def get_performance_config() -> PerformanceConfig:
    """Get performance configuration"""
    return performance_config

def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration"""
    return monitoring_config

def get_ui_config() -> UIConfig:
    """Get UI configuration"""
    return ui_config

def get_data_config() -> DataConfig:
    """Get data configuration"""
    return data_config

def get_all_configs() -> Dict[str, Any]:
    """Get all configurations as a dictionary"""
    return {
        'dashboard': dashboard_config,
        'security': security_config,
        'performance': performance_config,
        'monitoring': monitoring_config,
        'ui': ui_config,
        'data': data_config
    }

# Configuration update functions
def update_dashboard_config(**kwargs):
    """Update dashboard configuration"""
    for key, value in kwargs.items():
        if hasattr(dashboard_config, key):
            setattr(dashboard_config, key, value)

def update_security_config(**kwargs):
    """Update security configuration"""
    for key, value in kwargs.items():
        if hasattr(security_config, key):
            setattr(security_config, key, value)

def update_performance_config(**kwargs):
    """Update performance configuration"""
    for key, value in kwargs.items():
        if hasattr(performance_config, key):
            setattr(performance_config, key, value)

# Configuration export/import
def export_config_to_dict() -> Dict[str, Any]:
    """Export configuration to dictionary"""
    config_dict = {}
    
    for config_name, config_obj in get_all_configs().items():
        config_dict[config_name] = {}
        for field in config_obj.__dataclass_fields__:
            value = getattr(config_obj, field)
            if not field.startswith('_'):
                config_dict[config_name][field] = value
    
    return config_dict

def import_config_from_dict(config_dict: Dict[str, Any]):
    """Import configuration from dictionary"""
    for config_name, config_data in config_dict.items():
        if config_name == 'dashboard':
            update_dashboard_config(**config_data)
        elif config_name == 'security':
            update_security_config(**config_data)
        elif config_name == 'performance':
            update_performance_config(**config_data)
        elif config_name == 'monitoring':
            # Update monitoring config
            pass
        elif config_name == 'ui':
            # Update UI config
            pass
        elif config_name == 'data':
            # Update data config
            pass
