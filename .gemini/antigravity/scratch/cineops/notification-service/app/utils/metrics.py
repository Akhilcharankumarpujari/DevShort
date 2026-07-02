from prometheus_client import Counter, Histogram

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"]
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "endpoint"]
)

# Custom notification metrics
notifications_total = Counter("notifications_total", "Total notifications processed")
notification_success_total = Counter("notification_success_total", "Total successful notifications delivered")
notification_failure_total = Counter("notification_failure_total", "Total permanently failed notifications")
notification_retries_total = Counter("notification_retries_total", "Total notification delivery retries")
notification_latency_seconds = Histogram("notification_latency_seconds", "Latency of notification delivery in seconds")
