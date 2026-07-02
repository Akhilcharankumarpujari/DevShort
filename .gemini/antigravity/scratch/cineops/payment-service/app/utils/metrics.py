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

# Custom payment metrics
payments_total = Counter("payments_total", "Total payment intents created")
payment_success_total = Counter("payment_success_total", "Total successful payments")
payment_failure_total = Counter("payment_failure_total", "Total failed payments")
refunds_total = Counter("refunds_total", "Total refunds processed")
payment_duration_seconds = Histogram("payment_duration_seconds", "Duration of payment processing from PENDING to SUCCESS")
