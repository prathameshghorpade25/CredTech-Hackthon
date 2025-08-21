# CredTech XScore API Monitoring Guide

## Overview

This document provides a comprehensive guide to the monitoring and alerting system implemented in the CredTech XScore API. The monitoring system collects metrics about system resources, API performance, and application behavior to help identify issues, optimize performance, and ensure reliability.

## Monitoring Components

### 1. Metrics Collection

The monitoring system collects the following types of metrics:

#### System Metrics
- **CPU Usage**: Percentage of CPU utilization
- **Memory Usage**: Total, available, and used memory
- **Disk Usage**: Total, used, and free disk space

#### Application Metrics
- **Request Counts**: Number of requests by endpoint
- **Response Times**: Average response time by endpoint
- **Error Counts**: Number of errors by endpoint
- **Uptime**: API uptime in seconds

### 2. Alerting System

The monitoring system includes an alerting mechanism that triggers alerts when certain thresholds are exceeded:

- **High CPU Usage**: When CPU usage exceeds 80%
- **High Memory Usage**: When memory usage exceeds 80%
- **High Disk Usage**: When disk usage exceeds 80%
- **High Error Rate**: When the error rate exceeds 5% of requests
- **Slow Response Time**: When the average response time exceeds 1 second

### 3. Prometheus Integration

The API exposes metrics in Prometheus format, which can be scraped by a Prometheus server for long-term storage, visualization, and alerting.

## Accessing Metrics

### API Endpoints

The following endpoints are available for accessing metrics:

- **GET /api/metrics**: Get all metrics (system and application)
- **GET /api/metrics/system**: Get system metrics only
- **GET /api/metrics/application**: Get application metrics only

> **Note**: These endpoints require authentication with a JWT token and admin role.

### Prometheus Endpoint

Prometheus metrics are exposed at:

```
http://localhost:9090/metrics
```

This endpoint can be scraped by a Prometheus server to collect metrics over time.

## Monitoring Dashboard

For visualization of metrics, you can use Grafana with the following data sources:

1. **Prometheus**: For real-time metrics and alerting
2. **JSON API**: For custom metrics not available in Prometheus

A sample Grafana dashboard configuration is available in the `monitoring/grafana` directory.

## Configuration

### Environment Variables

The monitoring system can be configured using the following environment variables:

- `PROMETHEUS_PORT`: Port for the Prometheus metrics server (default: 9090)
- `METRICS_COLLECTION_INTERVAL`: Interval in seconds for collecting metrics (default: 60)
- `ALERT_CPU_THRESHOLD`: CPU usage threshold for alerts (default: 80)
- `ALERT_MEMORY_THRESHOLD`: Memory usage threshold for alerts (default: 80)
- `ALERT_DISK_THRESHOLD`: Disk usage threshold for alerts (default: 80)
- `ALERT_ERROR_RATE_THRESHOLD`: Error rate threshold for alerts (default: 0.05)
- `ALERT_RESPONSE_TIME_THRESHOLD`: Response time threshold for alerts in seconds (default: 1.0)

## Implementing Custom Alerts

You can implement custom alert callbacks by adding them to the metrics monitor:

```python
from src.utils.monitoring import metrics_monitor

def my_custom_alert_callback(alert_type, data):
    # Handle the alert
    print(f"Alert: {alert_type} - {data}")

# Add the callback
metrics_monitor.add_alert_callback(my_custom_alert_callback)
```

## Integration with External Monitoring Systems

### Prometheus and Grafana

1. Install Prometheus and Grafana
2. Configure Prometheus to scrape metrics from `http://localhost:9090/metrics`
3. Add Prometheus as a data source in Grafana
4. Import the sample dashboard from `monitoring/grafana/dashboard.json`

### ELK Stack

For log monitoring and analysis:

1. Configure Filebeat to collect logs from `logs/credtech_xscore_*.log`
2. Send logs to Elasticsearch
3. Create visualizations in Kibana

## Best Practices

1. **Regular Review**: Regularly review metrics and alerts to identify trends and potential issues
2. **Threshold Tuning**: Adjust alert thresholds based on observed patterns and requirements
3. **Correlation**: Correlate metrics with logs for better troubleshooting
4. **Capacity Planning**: Use historical metrics for capacity planning and scaling decisions
5. **Documentation**: Keep documentation updated with any changes to the monitoring system

## Troubleshooting

### Common Issues

1. **High CPU Usage**
   - Check for resource-intensive operations
   - Consider scaling up or optimizing code

2. **High Memory Usage**
   - Check for memory leaks
   - Consider increasing memory allocation or optimizing code

3. **High Error Rate**
   - Check logs for error details
   - Investigate and fix the root cause

4. **Slow Response Time**
   - Check database queries
   - Optimize code or add caching
   - Consider scaling up resources

## Conclusion

The monitoring system provides valuable insights into the health and performance of the CredTech XScore API. By regularly reviewing metrics and responding to alerts, you can ensure the reliability and performance of the API.