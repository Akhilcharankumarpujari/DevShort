import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { storageService } from "@/lib/services/storage";
import { mapFileToFrontend } from "@/lib/mappings";
import { getCurrentUser } from "@/lib/actions/user.actions";

// PATCH: Rename a file
export async function PATCH(
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
    const { name } = body;

    if (!name) {
      return NextResponse.json({ error: "Name is required" }, { status: 400 });
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

    // Update metadata name in database
    const updatedFile = await prisma.file.update({
      where: { id },
      data: { name },
      include: { owner: true },
    });

    return NextResponse.json(mapFileToFrontend(updatedFile));
  } catch (error) {
    console.error("Failed to rename file:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

// DELETE: Delete a file
export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

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

    // 1. Delete from S3/MinIO storage
    await storageService.deleteFile(file.storageKey);

    // 2. Delete from database
    await prisma.file.delete({
      where: { id },
    });

    return NextResponse.json({ status: "success" });
  } catch (error) {
    console.error("Failed to delete file:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
