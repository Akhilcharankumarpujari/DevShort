import logging
import json
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)
        return json.dumps(log_obj)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class LoggingAndMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        if path == "/metrics" or path == "/health":
            return await call_next(request)
            
        start_time = time.time()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logging.error(f"Request failed: {str(e)}", exc_info=True)
            raise e
        finally:
            duration = time.time() - start_time
            
            extra = {
                "extra_fields": {
                    "service": self.service_name,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            }
            if path.endswith("/lock-seats"):
                logging.info(f"Seat locked: {method} {path} processed", extra=extra)
            elif path.endswith("/confirm"):
                logging.info(f"Booking confirmed: {method} {path} processed", extra=extra)
            elif path.endswith("/cancel"):
                logging.info(f"Booking cancelled: {method} {path} processed", extra=extra)
            else:
                logging.info(f"Processed {method} {path} - {status_code}", extra=extra)
            
        return response
