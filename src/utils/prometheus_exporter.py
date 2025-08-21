"""Prometheus metrics exporter for CredTech XScore API"""

import os
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'credtech_api_requests_total',
    'Total number of requests by endpoint and status',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'credtech_api_request_latency_seconds',
    'Request latency in seconds by endpoint',
    ['endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

ERROR_COUNT = Counter(
    'credtech_api_errors_total',
    'Total number of errors by endpoint',
    ['endpoint']
)

SYSTEM_CPU_USAGE = Gauge(
    'credtech_system_cpu_usage',
    'Current CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'credtech_system_memory_usage_bytes',
    'Current memory usage in bytes'
)

SYSTEM_MEMORY_TOTAL = Gauge(
    'credtech_system_memory_total_bytes',
    'Total system memory in bytes'
)

SYSTEM_DISK_USAGE = Gauge(
    'credtech_system_disk_usage_bytes',
    'Current disk usage in bytes'
)

SYSTEM_DISK_TOTAL = Gauge(
    'credtech_system_disk_total_bytes',
    'Total disk space in bytes'
)

API_UPTIME = Gauge(
    'credtech_api_uptime_seconds',
    'API uptime in seconds'
)

MODEL_PREDICTION_LATENCY = Histogram(
    'credtech_model_prediction_latency_seconds',
    'Model prediction latency in seconds',
    ['model_version'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

MODEL_PREDICTION_COUNT = Counter(
    'credtech_model_predictions_total',
    'Total number of model predictions',
    ['model_version']
)


def record_request_metric(endpoint: str, status_code: int):
    """Record a request metric"""
    REQUEST_COUNT.labels(endpoint=endpoint, status=str(status_code)).inc()


def record_latency_metric(endpoint: str, latency: float):
    """Record a latency metric"""
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)


def record_error_metric(endpoint: str):
    """Record an error metric"""
    ERROR_COUNT.labels(endpoint=endpoint).inc()


def record_system_metrics(cpu_percent: float, memory_used: int, memory_total: int, 
                         disk_used: int, disk_total: int):
    """Record system metrics"""
    SYSTEM_CPU_USAGE.set(cpu_percent)
    SYSTEM_MEMORY_USAGE.set(memory_used)
    SYSTEM_MEMORY_TOTAL.set(memory_total)
    SYSTEM_DISK_USAGE.set(disk_used)
    SYSTEM_DISK_TOTAL.set(disk_total)


def record_uptime(uptime_seconds: float):
    """Record API uptime"""
    API_UPTIME.set(uptime_seconds)


def record_model_prediction(model_version: str, latency: float):
    """Record a model prediction metric"""
    MODEL_PREDICTION_LATENCY.labels(model_version=model_version).observe(latency)
    MODEL_PREDICTION_COUNT.labels(model_version=model_version).inc()


def start_prometheus_server(port: int = 9090):
    """Start the Prometheus metrics server"""
    # Get port from environment variable if available
    prometheus_port = int(os.environ.get('PROMETHEUS_PORT', port))
    
    # Start the server
    start_http_server(prometheus_port)
    print(f"Prometheus metrics server started on port {prometheus_port}")


# Initialize metrics on import
def init_metrics():
    """Initialize metrics with default values"""
    # Set initial values for gauges
    SYSTEM_CPU_USAGE.set(0)
    SYSTEM_MEMORY_USAGE.set(0)
    SYSTEM_MEMORY_TOTAL.set(0)
    SYSTEM_DISK_USAGE.set(0)
    SYSTEM_DISK_TOTAL.set(0)
    API_UPTIME.set(0)


# Initialize metrics
init_metrics()