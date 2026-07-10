import authService from "../services/auth.service.js";
import { BadRequestError } from "../utils/apiError.js";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN_LENGTH = 6;

function validateRegisterInput({ email, password, name }) {
  if (!email || !password || !name) {
    throw new BadRequestError("Email, password, and name are required");
  }

  if (typeof email !== "string" || !EMAIL_REGEX.test(email.trim())) {
    throw new BadRequestError("A valid email is required");
  }

  if (typeof password !== "string" || password.length < PASSWORD_MIN_LENGTH) {
    throw new BadRequestError(`Password must be at least ${PASSWORD_MIN_LENGTH} characters`);
  }

  if (typeof name !== "string" || name.trim().length === 0) {
    throw new BadRequestError("Name is required");
  }
}

function validateLoginInput({ email, password }) {
  if (!email || !password) {
    throw new BadRequestError("Email and password are required");
  }
}

async function register(req, res, next) {
  try {
    validateRegisterInput(req.body);

    const result = await authService.registerUser({
      email: req.body.email.trim().toLowerCase(),
      password: req.body.password,
      name: req.body.name.trim(),
    });

    res.status(201).json({
      data: {
        user: result.user,
        token: result.token,
      },
    });
  } catch (error) {
    next(error);
  }
}

async function login(req, res, next) {
  try {
    validateLoginInput(req.body);

    const result = await authService.loginUser({
      email: req.body.email.trim().toLowerCase(),
      password: req.body.password,
    });

    res.json({
      data: {
        user: result.user,
        token: result.token,
      },
    });
  } catch (error) {
    next(error);
  }
}

async function me(req, res, next) {
  try {
    const profile = await authService.getUserProfile(req.user.id);
    res.json({ data: profile });
  } catch (error) {
    next(error);
  }
}

export default { register, login, me };
