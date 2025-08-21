"""Tests for enhanced dashboard features"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
import time
import json
from datetime import datetime, timedelta

# Import dashboard components
from src.config.dashboard_config import (
    DashboardConfig, SecurityConfig, PerformanceConfig, 
    MonitoringConfig, UIConfig, DataConfig,
    validate_config, get_all_configs
)

class TestDashboardConfiguration(unittest.TestCase):
    """Test dashboard configuration classes"""
    
    def test_dashboard_config_defaults(self):
        """Test dashboard configuration default values"""
        config = DashboardConfig()
        
        self.assertEqual(config.app_name, "CredTech XScore")
        self.assertEqual(config.app_version, "1.0.0")
        self.assertFalse(config.debug_mode)
        self.assertTrue(config.enable_authentication)
        self.assertEqual(config.session_timeout_hours, 24)
        self.assertEqual(config.max_requests_per_minute, 60)
    
    def test_security_config_defaults(self):
        """Test security configuration default values"""
        config = SecurityConfig()
        
        self.assertEqual(config.min_password_length, 8)
        self.assertTrue(config.require_uppercase)
        self.assertTrue(config.require_lowercase)
        self.assertTrue(config.require_numbers)
        self.assertTrue(config.require_special_chars)
        self.assertTrue(config.enable_rate_limiting)
        self.assertEqual(config.rate_limit_max_requests, 60)
    
    def test_performance_config_defaults(self):
        """Test performance configuration default values"""
        config = PerformanceConfig()
        
        self.assertTrue(config.enable_lru_cache)
        self.assertEqual(config.lru_cache_max_size, 1000)
        self.assertTrue(config.enable_memory_cache)
        self.assertEqual(config.memory_cache_ttl, 300)
        self.assertTrue(config.enable_connection_pooling)
        self.assertEqual(config.max_database_connections, 20)
    
    def test_monitoring_config_defaults(self):
        """Test monitoring configuration default values"""
        config = MonitoringConfig()
        
        self.assertTrue(config.enable_metrics_collection)
        self.assertEqual(config.metrics_collection_interval, 60)
        self.assertTrue(config.enable_prometheus_export)
        self.assertEqual(config.prometheus_port, 8000)
        self.assertTrue(config.enable_health_checks)
        self.assertEqual(config.health_check_interval, 30)
    
    def test_ui_config_defaults(self):
        """Test UI configuration default values"""
        config = UIConfig()
        
        self.assertEqual(config.primary_color, "#2563EB")
        self.assertEqual(config.secondary_color, "#10B981")
        self.assertEqual(config.accent_color, "#F59E0B")
        self.assertTrue(config.enable_responsive_design)
        self.assertTrue(config.enable_mobile_optimization)
    
    def test_data_config_defaults(self):
        """Test data configuration default values"""
        config = DataConfig()
        
        self.assertTrue(config.enable_input_validation)
        self.assertTrue(config.enable_output_validation)
        self.assertEqual(config.max_input_length, 1000)
        self.assertEqual(config.max_file_size_mb, 10)
        self.assertTrue(config.enable_input_sanitization)
        self.assertTrue(config.enable_data_caching)
    
    def test_config_validation(self):
        """Test configuration validation"""
        errors = validate_config()
        self.assertEqual(len(errors), 0, f"Configuration validation errors: {errors}")
    
    def test_get_all_configs(self):
        """Test getting all configurations"""
        configs = get_all_configs()
        
        expected_keys = ['dashboard', 'security', 'performance', 'monitoring', 'ui', 'data']
        for key in expected_keys:
            self.assertIn(key, configs)
            self.assertIsNotNone(configs[key])

class TestSecurityFeatures(unittest.TestCase):
    """Test security features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session_state = {
            'authenticated': True,
            'username': 'testuser',
            'user_role': 'user',
            'session_id': 'test-session-123',
            'session_start': datetime.now().isoformat()
        }
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        from src.serve.app import check_rate_limit
        
        # Mock session state
        with patch('streamlit.session_state', self.mock_session_state):
            # First request should pass
            self.assertTrue(check_rate_limit('testuser', max_requests=5))
            
            # Make multiple requests to exceed limit
            for _ in range(5):
                check_rate_limit('testuser', max_requests=5)
            
            # Next request should fail
            self.assertFalse(check_rate_limit('testuser', max_requests=5))
    
    def test_session_validation(self):
        """Test session validation"""
        from src.serve.app import validate_session
        
        # Valid session
        self.assertTrue(validate_session(self.mock_session_state))
        
        # Invalid session - not authenticated
        invalid_session = self.mock_session_state.copy()
        invalid_session['authenticated'] = False
        self.assertFalse(validate_session(invalid_session))
        
        # Invalid session - expired
        expired_session = self.mock_session_state.copy()
        expired_session['session_start'] = (datetime.now() - timedelta(hours=25)).isoformat()
        self.assertFalse(validate_session(expired_session))
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        from src.utils.security import sanitize_input
        
        # Test string sanitization
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(dangerous_input)
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('</script>', sanitized)
        
        # Test dictionary sanitization
        dangerous_dict = {
            'name': '<script>alert("xss")</script>',
            'email': 'test@example.com'
        }
        sanitized_dict = sanitize_input(dangerous_dict)
        self.assertNotIn('<script>', sanitized_dict['name'])
        self.assertEqual(sanitized_dict['email'], 'test@example.com')

class TestPerformanceFeatures(unittest.TestCase):
    """Test performance features"""
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        from src.serve.app import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Test page timing
        monitor.start_page_timer('test_page')
        time.sleep(0.1)  # Simulate page load
        monitor.end_page_timer('test_page')
        
        # Test component timing
        start_time = monitor.start_component_timer('test_component')
        time.sleep(0.1)  # Simulate component render
        monitor.end_component_timer('test_component', start_time)
        
        # Get performance summary
        summary = monitor.get_performance_summary()
        
        self.assertIn('page_load_times', summary)
        self.assertIn('component_render_times', summary)
        self.assertGreater(summary['uptime_seconds'], 0)
    
    def test_caching(self):
        """Test caching functionality"""
        from src.utils.performance import lru_cache, cache_result
        
        # Test LRU cache
        lru_cache.put('test_key', 'test_value')
        self.assertEqual(lru_cache.get('test_key'), 'test_value')
        
        # Test cache decorator
        @cache_result(ttl=300)
        def test_function(x):
            return x * 2
        
        # First call should execute function
        result1 = test_function(5)
        self.assertEqual(result1, 10)
        
        # Second call should return cached result
        result2 = test_function(5)
        self.assertEqual(result2, 10)
    
    def test_performance_tracking_decorator(self):
        """Test performance tracking decorator"""
        from src.utils.performance import track_performance
        
        @track_performance("test_operation")
        def test_function():
            time.sleep(0.1)
            return "success"
        
        # Function should execute and log performance
        result = test_function()
        self.assertEqual(result, "success")

class TestMonitoringFeatures(unittest.TestCase):
    """Test monitoring features"""
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        from src.utils.monitoring import AdvancedMetricsCollector
        
        collector = AdvancedMetricsCollector()
        
        # Collect metrics
        metrics = collector.collect_advanced_metrics()
        
        # Check required fields
        required_fields = ['timestamp', 'cpu', 'memory', 'disk', 'requests', 'response_times', 'errors']
        for field in required_fields:
            self.assertIn(field, metrics)
        
        # Check alert generation
        alerts = metrics.get('alerts', [])
        self.assertIsInstance(alerts, list)
    
    def test_alert_thresholds(self):
        """Test alert threshold functionality"""
        from src.utils.monitoring import AdvancedMetricsCollector
        
        collector = AdvancedMetricsCollector()
        
        # Set custom threshold
        collector.set_alert_threshold('cpu_usage', 50.0)
        self.assertEqual(collector.alert_thresholds['cpu_usage'], 50.0)
        
        # Get alert history
        alerts = collector.get_alert_history(hours=1)
        self.assertIsInstance(alerts, list)
    
    def test_metrics_summary(self):
        """Test metrics summary generation"""
        from src.utils.monitoring import AdvancedMetricsCollector
        
        collector = AdvancedMetricsCollector()
        
        summary = collector.get_metrics_summary()
        
        required_fields = ['status', 'active_alerts', 'system_health', 'application_health', 'last_updated']
        for field in required_fields:
            self.assertIn(field, summary)
        
        # Status should be either 'healthy' or 'warning'
        self.assertIn(summary['status'], ['healthy', 'warning'])

class TestErrorHandling(unittest.TestCase):
    """Test error handling features"""
    
    def test_enhanced_error_handler(self):
        """Test enhanced error handler"""
        from src.serve.app import EnhancedErrorHandler
        
        handler = EnhancedErrorHandler()
        
        # Test error handling
        test_error = ValueError("Test error message")
        error_context = {'source': 'test', 'user': 'testuser'}
        
        error_id = handler.handle_error(test_error, error_context, show_to_user=False)
        
        # Check error was recorded
        self.assertIsInstance(error_id, str)
        self.assertEqual(len(error_id), 8)  # Short error ID
        
        # Check error history
        self.assertEqual(len(handler.error_history), 1)
        self.assertEqual(handler.error_history[0]['error_type'], 'ValueError')
        self.assertEqual(handler.error_history[0]['error_message'], 'Test error message')
        
        # Check error counts
        self.assertEqual(handler.error_counts['ValueError'], 1)

class TestUIEnhancements(unittest.TestCase):
    """Test UI enhancement features"""
    
    def test_responsive_design_config(self):
        """Test responsive design configuration"""
        config = UIConfig()
        
        # Check breakpoints
        self.assertEqual(config.breakpoint_small, 768)
        self.assertEqual(config.breakpoint_medium, 1024)
        self.assertEqual(config.breakpoint_large, 1200)
        
        # Check responsive features
        self.assertTrue(config.enable_responsive_design)
        self.assertTrue(config.enable_mobile_optimization)
    
    def test_theme_configuration(self):
        """Test theme configuration"""
        config = UIConfig()
        
        # Check color scheme
        self.assertIsInstance(config.primary_color, str)
        self.assertIsInstance(config.secondary_color, str)
        self.assertIsInstance(config.accent_color, str)
        self.assertIsInstance(config.error_color, str)
        self.assertIsInstance(config.warning_color, str)
        self.assertIsInstance(config.success_color, str)
        
        # Colors should be valid hex codes
        import re
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        for color in [config.primary_color, config.secondary_color, config.accent_color, 
                     config.error_color, config.warning_color, config.success_color]:
            self.assertIsNotNone(re.match(hex_pattern, color))

class TestDataHandling(unittest.TestCase):
    """Test data handling features"""
    
    def test_data_validation_config(self):
        """Test data validation configuration"""
        config = DataConfig()
        
        # Check validation settings
        self.assertTrue(config.enable_input_validation)
        self.assertTrue(config.enable_output_validation)
        self.assertTrue(config.enable_input_sanitization)
        self.assertTrue(config.enable_output_sanitization)
        
        # Check limits
        self.assertGreater(config.max_input_length, 0)
        self.assertGreater(config.max_file_size_mb, 0)
        self.assertGreater(config.max_storage_size_gb, 0)
    
    def test_caching_config(self):
        """Test caching configuration"""
        config = DataConfig()
        
        # Check caching settings
        self.assertTrue(config.enable_data_caching)
        self.assertGreater(config.cache_expiration_hours, 0)
        self.assertGreater(config.max_cached_items, 0)

# Integration tests
class TestDashboardIntegration(unittest.TestCase):
    """Integration tests for dashboard features"""
    
    def test_configuration_integration(self):
        """Test that all configurations work together"""
        # Get all configs
        configs = get_all_configs()
        
        # Check that all configs are properly initialized
        for config_name, config_obj in configs.items():
            self.assertIsNotNone(config_obj)
            self.assertTrue(hasattr(config_obj, '__dataclass_fields__'))
        
        # Validate configuration
        errors = validate_config()
        self.assertEqual(len(errors), 0, f"Configuration validation errors: {errors}")
    
    def test_security_performance_integration(self):
        """Test security and performance features working together"""
        from src.serve.app import check_rate_limit, validate_session
        
        # Mock session state
        session_state = {
            'authenticated': True,
            'username': 'testuser',
            'user_role': 'user',
            'session_start': datetime.now().isoformat()
        }
        
        # Both security checks should pass
        self.assertTrue(check_rate_limit('testuser', max_requests=10))
        self.assertTrue(validate_session(session_state))

# Performance tests
class TestDashboardPerformance(unittest.TestCase):
    """Performance tests for dashboard features"""
    
    def test_configuration_performance(self):
        """Test configuration loading performance"""
        import time
        
        start_time = time.time()
        
        # Load configurations multiple times
        for _ in range(100):
            configs = get_all_configs()
            _ = validate_config()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second)
        self.assertLess(execution_time, 1.0, f"Configuration operations took {execution_time:.3f}s")
    
    def test_error_handling_performance(self):
        """Test error handling performance"""
        from src.serve.app import EnhancedErrorHandler
        import time
        
        handler = EnhancedErrorHandler()
        
        start_time = time.time()
        
        # Handle multiple errors
        for i in range(100):
            error = ValueError(f"Test error {i}")
            handler.handle_error(error, {'source': 'test'}, show_to_user=False)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second)
        self.assertLess(execution_time, 1.0, f"Error handling took {execution_time:.3f}s")
        
        # Check error history size limit
        self.assertLessEqual(len(handler.error_history), 100)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
