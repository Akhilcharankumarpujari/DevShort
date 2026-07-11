import express from "express";
import helmet from "helmet";
import cors from "cors";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import config from "./config/index.js";
import routes from "./routes/index.js";
import errorHandler from "./middleware/errorHandler.js";
import { metricsMiddleware, metricsHandler } from "./middleware/metrics.js";

const app = express();

// Metrics endpoint — expose BEFORE helmet to avoid CSP blocking in dev tooling
// but AFTER it's safe; register before the rate limiter and route handlers.
app.get("/metrics", metricsHandler);

app.use(helmet());
app.use(
  cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (like mobile apps, curl, or server-to-server)
      if (!origin) return callback(null, true);
      
      if (config.corsOrigins.includes(origin)) {
        return callback(null, true);
      }
      return callback(new Error("Not allowed by CORS"));
    },
    credentials: true,
  })
);
app.use(morgan(config.nodeEnv === "production" ? "combined" : "dev"));
app.use(express.json({ limit: "1mb" }));

// Global metrics collection middleware (after morgan so response timing is captured)
app.use(metricsMiddleware);

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    error: {
      message: "Too many requests, please try again later",
      status: 429,
    },
  },
});

app.use("/api/urls", apiLimiter);
app.use(routes);

app.use((_req, _res, next) => {
  const err = new Error("Not found");
  err.statusCode = 404;
  next(err);
});

app.use(errorHandler);

export default app;
