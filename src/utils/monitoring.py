"""Monitoring utilities for CredTech XScore API"""

import os
import time
import logging
import psutil
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect and store system and application metrics"""
    
    def __init__(self, app_name: str = "credtech-api"):
        self.app_name = app_name
        self.metrics = {}
        self.start_time = time.time()
        self.request_counts = {}
        self.response_times = {}
        self.error_counts = {}
        self.last_collection_time = time.time()
        
        # Create metrics directory if it doesn't exist
        self.metrics_dir = Path("logs/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics like CPU, memory, and disk usage"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "used": psutil.disk_usage("/").used,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            },
        }
        
        return metrics
    
    def collect_app_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calculate request rate (requests per second)
        elapsed = current_time - self.last_collection_time
        request_rates = {}
        for endpoint, count in self.request_counts.items():
            request_rates[endpoint] = count / elapsed if elapsed > 0 else 0
        
        # Calculate average response times
        avg_response_times = {}
        for endpoint, times in self.response_times.items():
            if times:  # Check if the list is not empty
                avg_response_times[endpoint] = sum(times) / len(times)
            else:
                avg_response_times[endpoint] = 0
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime,
            "requests": {
                "total": sum(self.request_counts.values()),
                "by_endpoint": dict(self.request_counts),
                "rates": request_rates,
            },
            "response_times": {
                "average": avg_response_times,
            },
            "errors": {
                "total": sum(self.error_counts.values()),
                "by_endpoint": dict(self.error_counts),
            },
        }
        
        # Reset counters for next collection period
        self.request_counts = {k: 0 for k in self.request_counts}
        self.response_times = {k: [] for k in self.response_times}
        self.error_counts = {k: 0 for k in self.error_counts}
        self.last_collection_time = current_time
        
        return metrics
    
    def record_request(self, endpoint: str):
        """Record an API request"""
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
            self.response_times[endpoint] = []
            self.error_counts[endpoint] = 0
        
        self.request_counts[endpoint] += 1
    
    def record_response_time(self, endpoint: str, response_time: float):
        """Record API response time"""
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        
        self.response_times[endpoint].append(response_time)
    
    def record_error(self, endpoint: str):
        """Record an API error"""
        if endpoint not in self.error_counts:
            self.error_counts[endpoint] = 0
        
        self.error_counts[endpoint] += 1
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics (system and application)"""
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_app_metrics()
        
        all_metrics = {
            "timestamp": datetime.now().isoformat(),
            "app_name": self.app_name,
            "system": system_metrics,
            "application": app_metrics,
        }
        
        self.metrics = all_metrics
        return all_metrics
    
    def save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to a file"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = self.metrics_dir / f"metrics-{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(metrics, f, indent=2)


class AdvancedMetricsCollector(MetricsCollector):
    """Enhanced metrics collector with advanced features"""
    
    def __init__(self, app_name: str = "credtech-xscore"):
        super().__init__(app_name)
        self.performance_metrics = {}
        self.user_metrics = {}
        self.model_metrics = {}
        self.security_metrics = {}
        self.alert_thresholds = {}
        self.alert_history = []
        
        # Initialize alert thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default alert thresholds"""
        self.alert_thresholds = {
            'cpu_usage': 80.0,  # Alert if CPU > 80%
            'memory_usage': 85.0,  # Alert if memory > 85%
            'disk_usage': 90.0,  # Alert if disk > 90%
            'response_time': 5000,  # Alert if response time > 5s
            'error_rate': 0.05,  # Alert if error rate > 5%
            'request_rate': 1000,  # Alert if request rate > 1000 req/s
        }
    
    def collect_advanced_metrics(self) -> Dict[str, Any]:
        """Collect advanced application metrics"""
        basic_metrics = self.collect_app_metrics()
        system_metrics = self.collect_system_metrics()
        
        # Collect advanced metrics
        advanced_metrics = {
            "timestamp": datetime.now().isoformat(),
            "performance": self._collect_performance_metrics(),
            "user_activity": self._collect_user_metrics(),
            "model_performance": self._collect_model_metrics(),
            "security": self._collect_security_metrics(),
            "alerts": self._check_alerts(basic_metrics, system_metrics)
        }
        
        # Combine all metrics
        all_metrics = {
            **basic_metrics,
            **system_metrics,
            **advanced_metrics
        }
        
        # Store metrics for historical analysis
        self._store_metrics(all_metrics)
        
        return all_metrics
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect detailed performance metrics"""
        return {
            "page_load_times": self.performance_metrics.get('page_load_times', {}),
            "component_render_times": self.performance_metrics.get('component_render_times', {}),
            "database_query_times": self.performance_metrics.get('database_query_times', {}),
            "model_inference_times": self.performance_metrics.get('model_inference_times', {}),
            "memory_usage_trend": self._get_memory_trend(),
            "cpu_usage_trend": self._get_cpu_trend()
        }
    
    def _collect_user_metrics(self) -> Dict[str, Any]:
        """Collect user activity metrics"""
        return {
            "active_sessions": len(self.user_metrics.get('active_sessions', [])),
            "total_users": self.user_metrics.get('total_users', 0),
            "page_views": self.user_metrics.get('page_views', {}),
            "user_actions": self.user_metrics.get('user_actions', {}),
            "session_durations": self.user_metrics.get('session_durations', []),
            "user_retention": self._calculate_user_retention()
        }
    
    def _collect_model_metrics(self) -> Dict[str, Any]:
        """Collect model performance metrics"""
        return {
            "prediction_accuracy": self.model_metrics.get('prediction_accuracy', 0.0),
            "model_latency": self.model_metrics.get('model_latency', {}),
            "feature_importance": self.model_metrics.get('feature_importance', {}),
            "model_versions": self.model_metrics.get('model_versions', []),
            "drift_detection": self._detect_model_drift()
        }
    
    def _collect_security_metrics(self) -> Dict[str, Any]:
        """Collect security-related metrics"""
        return {
            "failed_logins": self.security_metrics.get('failed_logins', 0),
            "suspicious_activities": self.security_metrics.get('suspicious_activities', []),
            "rate_limit_violations": self.security_metrics.get('rate_limit_violations', 0),
            "authentication_events": self.security_metrics.get('authentication_events', {}),
            "authorization_failures": self.security_metrics.get('authorization_failures', 0)
        }
    
    def _check_alerts(self, app_metrics: Dict, system_metrics: Dict) -> List[Dict]:
        """Check for alert conditions and generate alerts"""
        alerts = []
        current_time = datetime.now()
        
        # Check CPU usage
        if system_metrics['cpu']['usage_percent'] > self.alert_thresholds['cpu_usage']:
            alerts.append({
                'timestamp': current_time.isoformat(),
                'level': 'warning',
                'type': 'high_cpu_usage',
                'message': f"CPU usage is {system_metrics['cpu']['usage_percent']:.1f}%",
                'value': system_metrics['cpu']['usage_percent'],
                'threshold': self.alert_thresholds['cpu_usage']
            })
        
        # Check memory usage
        if system_metrics['memory']['percent'] > self.alert_thresholds['memory_usage']:
            alerts.append({
                'timestamp': current_time.isoformat(),
                'level': 'warning',
                'type': 'high_memory_usage',
                'message': f"Memory usage is {system_metrics['memory']['percent']:.1f}%",
                'value': system_metrics['memory']['percent'],
                'threshold': self.alert_thresholds['memory_usage']
            })
        
        # Check error rate
        total_requests = app_metrics['requests']['total']
        total_errors = app_metrics['errors']['total']
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'timestamp': current_time.isoformat(),
                    'level': 'critical',
                    'type': 'high_error_rate',
                    'message': f"Error rate is {error_rate:.2%}",
                    'value': error_rate,
                    'threshold': self.alert_thresholds['error_rate']
                })
        
        # Store alerts
        for alert in alerts:
            self.alert_history.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        return alerts
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics for historical analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    def _get_memory_trend(self) -> List[float]:
        """Get memory usage trend over time"""
        # This would typically come from historical data
        # For now, return a simple trend
        return [psutil.virtual_memory().percent]
    
    def _get_cpu_trend(self) -> List[float]:
        """Get CPU usage trend over time"""
        # This would typically come from historical data
        # For now, return a simple trend
        return [psutil.cpu_percent(interval=1)]
    
    def _calculate_user_retention(self) -> float:
        """Calculate user retention rate"""
        # This would typically calculate based on historical data
        # For now, return a placeholder
        return 0.85
    
    def _detect_model_drift(self) -> Dict[str, Any]:
        """Detect model performance drift"""
        # This would implement actual drift detection logic
        # For now, return a placeholder
        return {
            "drift_detected": False,
            "confidence": 0.95,
            "last_check": datetime.now().isoformat()
        }
    
    def set_alert_threshold(self, metric: str, threshold: float):
        """Set custom alert threshold for a metric"""
        if metric in self.alert_thresholds:
            self.alert_thresholds[metric] = threshold
            logger.info(f"Alert threshold for {metric} set to {threshold}")
        else:
            logger.warning(f"Unknown metric: {metric}")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Get alert history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        current_metrics = self.collect_advanced_metrics()
        
        return {
            "status": "healthy" if not current_metrics['alerts'] else "warning",
            "active_alerts": len(current_metrics['alerts']),
            "system_health": {
                "cpu_usage": current_metrics['cpu']['usage_percent'],
                "memory_usage": current_metrics['memory']['percent'],
                "disk_usage": current_metrics['disk']['percent']
            },
            "application_health": {
                "uptime": current_metrics['uptime'],
                "total_requests": current_metrics['requests']['total'],
                "error_rate": current_metrics['errors']['total'] / max(current_metrics['requests']['total'], 1)
            },
            "last_updated": current_metrics['timestamp']
        }


class MetricsMonitor:
    """Monitor metrics and trigger alerts"""
    
    def __init__(self, collector: MetricsCollector, collection_interval: int = 60):
        self.collector = collector
        self.collection_interval = collection_interval
        
        # Load thresholds from environment variables or use defaults
        self.alert_thresholds = {
            "cpu_percent": float(os.environ.get("ALERT_CPU_THRESHOLD", 80.0)),
            "memory_percent": float(os.environ.get("ALERT_MEMORY_THRESHOLD", 80.0)),
            "disk_percent": float(os.environ.get("ALERT_DISK_THRESHOLD", 80.0)),
            "error_rate": float(os.environ.get("ALERT_ERROR_RATE_THRESHOLD", 0.05)),  # 5% of requests
            "response_time": float(os.environ.get("ALERT_RESPONSE_TIME_THRESHOLD", 1.0)),  # 1 second
        }
        self.alert_callbacks = []
        self.running = False
        self.monitor_thread = None
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "data": data,
        }
        
        # Log the alert
        logger.warning(f"Alert triggered: {alert_type} - {data}")
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                logger.error(f"Error in alert callback: {str(e)}")
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts"""
        # Check CPU usage
        cpu_percent = metrics["system"]["cpu"]["usage_percent"]
        if cpu_percent > self.alert_thresholds["cpu_percent"]:
            self.trigger_alert("high_cpu_usage", {
                "current": cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
            })
        
        # Check memory usage
        memory_percent = metrics["system"]["memory"]["percent"]
        if memory_percent > self.alert_thresholds["memory_percent"]:
            self.trigger_alert("high_memory_usage", {
                "current": memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
            })
        
        # Check disk usage
        disk_percent = metrics["system"]["disk"]["percent"]
        if disk_percent > self.alert_thresholds["disk_percent"]:
            self.trigger_alert("high_disk_usage", {
                "current": disk_percent,
                "threshold": self.alert_thresholds["disk_percent"],
            })
        
        # Check error rates
        total_requests = metrics["application"]["requests"]["total"]
        total_errors = metrics["application"]["errors"]["total"]
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.alert_thresholds["error_rate"]:
                self.trigger_alert("high_error_rate", {
                    "current": error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                    "total_errors": total_errors,
                    "total_requests": total_requests,
                })
        
        # Check response times
        for endpoint, avg_time in metrics["application"]["response_times"]["average"].items():
            if avg_time > self.alert_thresholds["response_time"]:
                self.trigger_alert("slow_response_time", {
                    "endpoint": endpoint,
                    "current": avg_time,
                    "threshold": self.alert_thresholds["response_time"],
                })
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = self.collector.collect_all_metrics()
                
                # Save metrics to file
                self.collector.save_metrics(metrics)
                
                # Check for alerts
                self.check_alerts(metrics)
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.collection_interval)
    
    def start(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info(f"Metrics monitoring started with interval {self.collection_interval}s")
    
    def stop(self):
        """Stop the monitoring thread"""
        if self.running:
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5.0)
            logger.info("Metrics monitoring stopped")


# Default alert callbacks
def log_alert_callback(alert_type: str, data: Dict[str, Any]):
    """Log alerts to a file"""
    alert_log_dir = Path("logs/alerts")
    alert_log_dir.mkdir(parents=True, exist_ok=True)
    
    alert_log_file = alert_log_dir / "alerts.log"
    
    with open(alert_log_file, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {alert_type}: {json.dumps(data)}\n")


# Create a global metrics collector and monitor
metrics_collector = AdvancedMetricsCollector()
metrics_monitor = MetricsMonitor(metrics_collector)

# Add default alert callbacks
metrics_monitor.add_alert_callback(log_alert_callback)


def start_monitoring(collection_interval: int = 60):
    """Start monitoring with the specified collection interval"""
    global metrics_monitor
    metrics_monitor.collection_interval = collection_interval
    metrics_monitor.start()


def stop_monitoring():
    """Stop monitoring"""
    global metrics_monitor
    metrics_monitor.stop()


def get_current_metrics() -> Dict[str, Any]:
    """Get the current metrics"""
    global metrics_collector
    return metrics_collector.collect_all_metrics()


def record_request(endpoint: str):
    """Record an API request"""
    global metrics_collector
    metrics_collector.record_request(endpoint)


def record_response_time(endpoint: str, response_time: float):
    """Record API response time"""
    global metrics_collector
    metrics_collector.record_response_time(endpoint, response_time)


def record_error(endpoint: str):
    """Record an API error"""
    global metrics_collector
    metrics_collector.record_error(endpoint)
