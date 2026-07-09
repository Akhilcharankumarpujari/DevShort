import { ApiError } from "../utils/apiError.js";

function errorHandler(err, _req, res, _next) {
  if (err instanceof ApiError) {
    return res.status(err.statusCode).json({
      error: {
        message: err.message,
        status: err.statusCode,
      },
    });
  }

  if (err.code === "P2025") {
    return res.status(404).json({
      error: {
        message: "Resource not found",
        status: 404,
      },
    });
  }

  if (err.code === "P2002") {
    return res.status(409).json({
      error: {
        message: "A record with that value already exists",
        status: 409,
      },
    });
  }

  console.error("Unhandled error:", err);

  const isProduction = process.env.NODE_ENV === "production";

  res.status(500).json({
    error: {
      message: isProduction ? "Internal server error" : err.message,
      status: 500,
      ...(isProduction ? {} : { stack: err.stack }),
    },
  });
}

export default errorHandler;
