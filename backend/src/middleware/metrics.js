import client from "prom-client";

// Create a Registry to register metrics
const register = new client.Registry();

// Enable default metrics collection (CPU, memory, event loop, GC, etc.)
// Prefix all default metrics with "devshort_"
client.collectDefaultMetrics({
  register,
  prefix: "devshort_",
});

// ---------------------------------------------------------------------------
// Custom HTTP metrics
// ---------------------------------------------------------------------------

export const httpRequestCounter = new client.Counter({
  name: "devshort_http_requests_total",
  help: "Total number of HTTP requests",
  labelNames: ["method", "route", "status_code"],
  registers: [register],
});

export const httpRequestDuration = new client.Histogram({
  name: "devshort_http_request_duration_seconds",
  help: "Duration of HTTP requests in seconds",
  labelNames: ["method", "route", "status_code"],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register],
});

export const httpResponseSize = new client.Summary({
  name: "devshort_http_response_size_bytes",
  help: "Response size in bytes",
  labelNames: ["method", "route", "status_code"],
  registers: [register],
});

// ---------------------------------------------------------------------------
// Express middleware — collects per-request metrics
// ---------------------------------------------------------------------------

export function metricsMiddleware(req, res, next) {
  // Skip metrics endpoint itself to avoid self-referential noise
  if (req.path === "/metrics") {
    return next();
  }

  const start = process.hrtime.bigint();
  const endTimer = httpRequestDuration.startTimer();

  // Capture the response finish event
  res.on("finish", () => {
    const durationSec =
      Number(process.hrtime.bigint() - start) / 1_000_000_000;

    const route = req.route?.path || req.path;
    const labels = {
      method: req.method,
      route,
      status_code: String(res.statusCode),
    };

    httpRequestCounter.inc(labels);

    endTimer(labels);

    // Record response size from Content-Length header
    const contentLength = parseInt(res.getHeader("content-length"), 10);
    if (!Number.isNaN(contentLength)) {
      httpResponseSize.observe(labels, contentLength);
    }
  });

  next();
}

// ---------------------------------------------------------------------------
// GET /metrics handler
// ---------------------------------------------------------------------------

export async function metricsHandler(_req, res) {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
}

export default register;
