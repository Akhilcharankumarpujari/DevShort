"use server";

import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { verifyToken } from "@/lib/services/jwt";
import { revalidatePath } from "next/cache";

const handleError = (error: unknown, message: string) => {
  console.error(message, error);
  throw error;
};

/**
 * Gets the currently authenticated user by reading and verifying the JWT cookie.
 */
export const getCurrentUser = async () => {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("session-token")?.value;

    if (!token) return null;

    // Verify token
    const payload = verifyToken(token);
    if (!payload) return null;

    // Fetch user from DB
    const user = await prisma.user.findUnique({
      where: { id: payload.userId },
    });

    if (!user) return null;

    // Return mapped object for frontend compatibility
    return {
      $id: user.id,
      accountId: user.id,
      fullName: user.fullName,
      email: user.email,
      avatar: user.avatar || "",
    };
  } catch (error) {
    console.error("Error in getCurrentUser:", error);
    return null;
  }
};

/**
 * Signs out the user by clearing the JWT session-token cookie
 */
export const signOutUser = async () => {
  try {
    const cookieStore = await cookies();
    cookieStore.delete("session-token");
  } catch (error) {
    handleError(error, "Failed to sign out user");
  }
  
  redirect("/sign-in");
};

/**
 * Revalidates cache for a specific path
 */
export const revalidatePathAction = async (path: string) => {
  revalidatePath(path);
};
