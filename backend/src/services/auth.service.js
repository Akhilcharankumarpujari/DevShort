import bcrypt from "bcryptjs";
import prisma from "../lib/prisma.js";
import { signToken } from "../utils/jwt.js";
import { ConflictError, UnauthorizedError } from "../utils/apiError.js";

const SALT_ROUNDS = 12;

export async function registerUser({ email, password, name }) {
  const existing = await prisma.user.findUnique({ where: { email } });

  if (existing) {
    throw new ConflictError("A user with this email already exists");
  }

  const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

  const user = await prisma.user.create({
    data: { email, passwordHash, name },
  });

  const token = signToken({ sub: user.id, email: user.email });

  return {
    user: { id: user.id, email: user.email, name: user.name, createdAt: user.createdAt },
    token,
  };
}

export async function loginUser({ email, password }) {
  const user = await prisma.user.findUnique({ where: { email } });

  if (!user) {
    throw new UnauthorizedError("Invalid email or password");
  }

  const valid = await bcrypt.compare(password, user.passwordHash);

  if (!valid) {
    throw new UnauthorizedError("Invalid email or password");
  }

  const token = signToken({ sub: user.id, email: user.email });

  return {
    user: { id: user.id, email: user.email, name: user.name, createdAt: user.createdAt },
    token,
  };
}

export async function getUserProfile(userId) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      email: true,
      name: true,
      createdAt: true,
      _count: { select: { urls: true } },
    },
  });

  if (!user) {
    throw new UnauthorizedError("User not found");
  }

  return {
    id: user.id,
    email: user.email,
    name: user.name,
    createdAt: user.createdAt,
    totalUrls: user._count.urls,
  };
}

export default {
  registerUser,
  loginUser,
  getUserProfile,
};

