import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { hashPassword } from "@/lib/services/password";
import { z } from "zod";

const signupSchema = z.object({
  fullName: z.string().min(2, "Full name must be at least 2 characters").max(50),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    // 1. Validate fields with Zod
    const validationResult = signupSchema.safeParse(body);
    if (!validationResult.success) {
      const errorMsg = validationResult.error.errors[0]?.message || "Validation error";
      return NextResponse.json({ error: errorMsg }, { status: 400 });
    }

    const { fullName, email, password } = validationResult.data;

    // 2. Check for duplicate email
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return NextResponse.json({ error: "Email already exists" }, { status: 409 });
    }

    // 3. Hash the password
    const hashedPassword = await hashPassword(password);

    // Default avatar placeholder URL
    const avatarPlaceholderUrl = "https://img.freepik.com/free-psd/3d-illustration-person-with-glasses_23-2149436185.jpg";

    // 4. Create user in database
    const newUser = await prisma.user.create({
      data: {
        fullName,
        email,
        password: hashedPassword,
        avatar: avatarPlaceholderUrl,
      },
    });

    return NextResponse.json({
      success: true,
      user: {
        id: newUser.id,
        fullName: newUser.fullName,
        email: newUser.email,
      },
    });
  } catch (error) {
    console.error("Signup error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
