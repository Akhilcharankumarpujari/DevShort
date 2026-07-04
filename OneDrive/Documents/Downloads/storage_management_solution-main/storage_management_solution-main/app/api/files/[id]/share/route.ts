import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mapFileToFrontend } from "@/lib/mappings";
import { getCurrentUser } from "@/lib/actions/user.actions";

// POST: Update file sharing users list
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const body = await req.json();
    const { emails } = body;

    if (!Array.isArray(emails)) {
      return NextResponse.json({ error: "Emails list must be an array" }, { status: 400 });
    }

    // Verify file existence and ownership
    const file = await prisma.file.findUnique({
      where: { id },
      include: { owner: true },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    if (file.owner.email !== currentUser.email) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Update shared user list in database
    const updatedFile = await prisma.file.update({
      where: { id },
      data: {
        users: emails,
      },
      include: {
        owner: true,
      },
    });

    return NextResponse.json(mapFileToFrontend(updatedFile));
  } catch (error) {
    console.error("Failed to share file:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
