import { verifyToken } from "../utils/jwt.js";
import { UnauthorizedError } from "../utils/apiError.js";

export function authenticate(req, _res, next) {
  try {
    const header = req.headers.authorization;

    if (!header || !header.startsWith("Bearer ")) {
      throw new UnauthorizedError("Authentication required");
    }

    const token = header.split(" ")[1];
    const decoded = verifyToken(token);

    req.user = { id: decoded.sub, email: decoded.email };
    next();
  } catch (error) {
    if (error.name === "JsonWebTokenError" || error.name === "TokenExpiredError") {
      next(new UnauthorizedError("Invalid or expired token"));
    } else {
      next(error);
    }
  }
}

export function optionalAuth(req, _res, next) {
  try {
    const header = req.headers.authorization;

    if (header && header.startsWith("Bearer ")) {
      const token = header.split(" ")[1];
      const decoded = verifyToken(token);
      req.user = { id: decoded.sub, email: decoded.email };
    }
  } catch {
    // Token invalid or expired — proceed without user
  }

  next();
}
