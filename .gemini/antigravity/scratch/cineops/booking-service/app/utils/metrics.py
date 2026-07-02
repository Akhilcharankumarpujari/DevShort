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

# Custom booking metrics
bookings_total = Counter("bookings_total", "Total booking attempts")
booking_success_total = Counter("booking_success_total", "Total successful bookings")
booking_failure_total = Counter("booking_failure_total", "Total failed bookings")
booking_cancellation_total = Counter("booking_cancellation_total", "Total cancelled bookings")
seat_locks_total = Counter("seat_locks_total", "Total seats locked")
booking_time_seconds = Histogram("booking_time_seconds", "Time taken to complete a booking from lock to confirm")
