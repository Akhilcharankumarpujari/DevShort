class ApiError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

class NotFoundError extends ApiError {
  constructor(message = "Resource not found") {
    super(404, message);
  }
}

class BadRequestError extends ApiError {
  constructor(message = "Bad request") {
    super(400, message);
  }
}

class ConflictError extends ApiError {
  constructor(message = "Conflict") {
    super(409, message);
  }
}

class UnauthorizedError extends ApiError {
  constructor(message = "Unauthorized") {
    super(401, message);
  }
}

class ForbiddenError extends ApiError {
  constructor(message = "Forbidden") {
    super(403, message);
  }
}

export { ApiError, NotFoundError, BadRequestError, ConflictError, UnauthorizedError, ForbiddenError };
