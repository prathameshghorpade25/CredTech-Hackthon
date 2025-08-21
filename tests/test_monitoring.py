"""Tests for the monitoring system"""

import unittest
import time
from unittest.mock import patch, MagicMock

from src.utils.monitoring import (
    MetricsCollector, MetricsMonitor, 
    record_request, record_response_time, record_error,
    get_current_metrics
)


class TestMetricsCollector(unittest.TestCase):
    """Test the MetricsCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector(app_name="test-app")
    
    def test_record_request(self):
        """Test recording a request"""
        endpoint = "/api/test"
        self.collector.record_request(endpoint)
        self.assertEqual(self.collector.request_counts[endpoint], 1)
        
        # Record another request
        self.collector.record_request(endpoint)
        self.assertEqual(self.collector.request_counts[endpoint], 2)
    
    def test_record_response_time(self):
        """Test recording response time"""
        endpoint = "/api/test"
        response_time = 0.5
        self.collector.record_response_time(endpoint, response_time)
        self.assertEqual(self.collector.response_times[endpoint], [response_time])
        
        # Record another response time
        self.collector.record_response_time(endpoint, response_time * 2)
        self.assertEqual(self.collector.response_times[endpoint], [response_time, response_time * 2])
    
    def test_record_error(self):
        """Test recording an error"""
        endpoint = "/api/test"
        self.collector.record_error(endpoint)
        self.assertEqual(self.collector.error_counts[endpoint], 1)
        
        # Record another error
        self.collector.record_error(endpoint)
        self.assertEqual(self.collector.error_counts[endpoint], 2)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        """Test collecting system metrics"""
        # Mock psutil functions
        mock_cpu_percent.return_value = 50.0
        mock_virtual_memory.return_value = MagicMock(
            total=16000000000,
            available=8000000000,
            used=8000000000,
            percent=50.0
        )
        mock_disk_usage.return_value = MagicMock(
            total=100000000000,
            used=50000000000,
            free=50000000000,
            percent=50.0
        )
        
        # Collect system metrics
        metrics = self.collector.collect_system_metrics()
        
        # Check metrics
        self.assertEqual(metrics['cpu']['usage_percent'], 50.0)
        self.assertEqual(metrics['memory']['total'], 16000000000)
        self.assertEqual(metrics['memory']['available'], 8000000000)
        self.assertEqual(metrics['memory']['used'], 8000000000)
        self.assertEqual(metrics['memory']['percent'], 50.0)
        self.assertEqual(metrics['disk']['total'], 100000000000)
        self.assertEqual(metrics['disk']['used'], 50000000000)
        self.assertEqual(metrics['disk']['free'], 50000000000)
        self.assertEqual(metrics['disk']['percent'], 50.0)
    
    def test_collect_app_metrics(self):
        """Test collecting application metrics"""
        # Record some metrics
        endpoint1 = "/api/test1"
        endpoint2 = "/api/test2"
        self.collector.record_request(endpoint1)
        self.collector.record_request(endpoint1)
        self.collector.record_request(endpoint2)
        self.collector.record_response_time(endpoint1, 0.5)
        self.collector.record_response_time(endpoint1, 1.5)
        self.collector.record_response_time(endpoint2, 1.0)
        self.collector.record_error(endpoint1)
        
        # Collect application metrics
        metrics = self.collector.collect_app_metrics()
        
        # Check metrics
        self.assertEqual(metrics['requests']['total'], 3)
        self.assertEqual(metrics['requests']['by_endpoint'][endpoint1], 0)
        self.assertEqual(metrics['requests']['by_endpoint'][endpoint2], 0)
        self.assertEqual(len(metrics['response_times']['average']), 2)
        self.assertEqual(metrics['errors']['total'], 0)
        self.assertEqual(metrics['errors']['by_endpoint'][endpoint1], 0)
    
    def test_collect_all_metrics(self):
        """Test collecting all metrics"""
        # Mock system and app metrics
        with patch.object(self.collector, 'collect_system_metrics') as mock_system_metrics, \
             patch.object(self.collector, 'collect_app_metrics') as mock_app_metrics:
            mock_system_metrics.return_value = {'cpu': {'usage_percent': 50.0}}
            mock_app_metrics.return_value = {'requests': {'total': 3}}
            
            # Collect all metrics
            metrics = self.collector.collect_all_metrics()
            
            # Check metrics
            self.assertEqual(metrics['app_name'], 'test-app')
            self.assertEqual(metrics['system'], {'cpu': {'usage_percent': 50.0}})
            self.assertEqual(metrics['application'], {'requests': {'total': 3}})


class TestMetricsMonitor(unittest.TestCase):
    """Test the MetricsMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector(app_name="test-app")
        self.monitor = MetricsMonitor(self.collector, collection_interval=1)
    
    def test_add_alert_callback(self):
        """Test adding an alert callback"""
        callback = lambda alert_type, data: None
        self.monitor.add_alert_callback(callback)
        self.assertEqual(len(self.monitor.alert_callbacks), 1)
    
    def test_trigger_alert(self):
        """Test triggering an alert"""
        # Mock callback
        mock_callback = MagicMock()
        self.monitor.add_alert_callback(mock_callback)
        
        # Trigger alert
        alert_type = "test_alert"
        alert_data = {"test": "data"}
        self.monitor.trigger_alert(alert_type, alert_data)
        
        # Check callback was called
        mock_callback.assert_called_once_with(alert_type, alert_data)
    
    def test_check_alerts_cpu(self):
        """Test checking CPU alerts"""
        # Mock trigger_alert
        with patch.object(self.monitor, 'trigger_alert') as mock_trigger_alert:
            # Set CPU usage above threshold
            metrics = {
                "system": {
                    "cpu": {"usage_percent": 90.0},
                    "memory": {"percent": 50.0},
                    "disk": {"percent": 50.0}
                },
                "application": {
                    "requests": {"total": 100},
                    "errors": {"total": 0},
                    "response_times": {"average": {}}
                }
            }
            
            # Check alerts
            self.monitor.check_alerts(metrics)
            
            # Check trigger_alert was called
            mock_trigger_alert.assert_called_once_with("high_cpu_usage", {
                "current": 90.0,
                "threshold": 80.0
            })
    
    def test_check_alerts_memory(self):
        """Test checking memory alerts"""
        # Mock trigger_alert
        with patch.object(self.monitor, 'trigger_alert') as mock_trigger_alert:
            # Set memory usage above threshold
            metrics = {
                "system": {
                    "cpu": {"usage_percent": 50.0},
                    "memory": {"percent": 90.0},
                    "disk": {"percent": 50.0}
                },
                "application": {
                    "requests": {"total": 100},
                    "errors": {"total": 0},
                    "response_times": {"average": {}}
                }
            }
            
            # Check alerts
            self.monitor.check_alerts(metrics)
            
            # Check trigger_alert was called
            mock_trigger_alert.assert_called_once_with("high_memory_usage", {
                "current": 90.0,
                "threshold": 80.0
            })
    
    def test_check_alerts_error_rate(self):
        """Test checking error rate alerts"""
        # Mock trigger_alert
        with patch.object(self.monitor, 'trigger_alert') as mock_trigger_alert:
            # Set error rate above threshold
            metrics = {
                "system": {
                    "cpu": {"usage_percent": 50.0},
                    "memory": {"percent": 50.0},
                    "disk": {"percent": 50.0}
                },
                "application": {
                    "requests": {"total": 100},
                    "errors": {"total": 10},
                    "response_times": {"average": {}}
                }
            }
            
            # Check alerts
            self.monitor.check_alerts(metrics)
            
            # Check trigger_alert was called
            mock_trigger_alert.assert_called_once_with("high_error_rate", {
                "current": 0.1,
                "threshold": 0.05,
                "total_errors": 10,
                "total_requests": 100
            })
    
    def test_start_stop(self):
        """Test starting and stopping the monitor"""
        # Start monitor
        self.monitor.start()
        self.assertTrue(self.monitor.running)
        self.assertIsNotNone(self.monitor.monitor_thread)
        
        # Stop monitor
        self.monitor.stop()
        self.assertFalse(self.monitor.running)


class TestMonitoringFunctions(unittest.TestCase):
    """Test the monitoring functions"""
    
    @patch('src.utils.monitoring.metrics_collector')
    def test_record_request(self, mock_collector):
        """Test recording a request"""
        endpoint = "/api/test"
        record_request(endpoint)
        mock_collector.record_request.assert_called_once_with(endpoint)
    
    @patch('src.utils.monitoring.metrics_collector')
    def test_record_response_time(self, mock_collector):
        """Test recording response time"""
        endpoint = "/api/test"
        response_time = 0.5
        record_response_time(endpoint, response_time)
        mock_collector.record_response_time.assert_called_once_with(endpoint, response_time)
    
    @patch('src.utils.monitoring.metrics_collector')
    def test_record_error(self, mock_collector):
        """Test recording an error"""
        endpoint = "/api/test"
        record_error(endpoint)
        mock_collector.record_error.assert_called_once_with(endpoint)
    
    @patch('src.utils.monitoring.metrics_collector')
    def test_get_current_metrics(self, mock_collector):
        """Test getting current metrics"""
        mock_metrics = {"test": "metrics"}
        mock_collector.collect_all_metrics.return_value = mock_metrics
        metrics = get_current_metrics()
        self.assertEqual(metrics, mock_metrics)


if __name__ == "__main__":
    unittest.main()