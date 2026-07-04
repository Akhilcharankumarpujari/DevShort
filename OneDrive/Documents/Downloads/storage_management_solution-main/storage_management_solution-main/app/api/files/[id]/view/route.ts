import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { storageService } from "@/lib/services/storage";
import { getCurrentUser } from "@/lib/actions/user.actions";

// GET: Stream file for viewing in new tab/viewer
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return new Response("Unauthorized", { status: 401 });
    }

    const { id } = await params;

    // Verify file exists and user has access (owner or shared with)
    const file = await prisma.file.findUnique({
      where: { id },
      include: { owner: true },
    });

    if (!file) {
      return new Response("File not found", { status: 404 });
    }

    const hasAccess =
      file.owner.email === currentUser.email ||
      file.users.includes(currentUser.email);

    if (!hasAccess) {
      return new Response("Forbidden", { status: 403 });
    }

    // Get stream from storage
    const s3Object = await storageService.getFileStream(file.storageKey);

    if (!s3Object.Body) {
      return new Response("File content is empty", { status: 404 });
    }

    const response = new NextResponse(s3Object.Body as any, {
      status: 200,
    });

    // Set proper content headers
    response.headers.set("Content-Type", s3Object.ContentType || "application/octet-stream");
    if (s3Object.ContentLength) {
      response.headers.set("Content-Length", s3Object.ContentLength.toString());
    }

    return response;
  } catch (error) {
    console.error("Failed to view file:", error);
    return new Response("Internal Server Error", { status: 500 });
  }
}
