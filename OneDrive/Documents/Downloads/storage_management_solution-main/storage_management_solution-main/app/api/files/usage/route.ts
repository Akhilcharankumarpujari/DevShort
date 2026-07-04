import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getCurrentUser } from "@/lib/actions/user.actions";

// GET: Calculate user's file space usage grouped by type
export async function GET(req: NextRequest) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Find all files owned by the user
    const files = await prisma.file.findMany({
      where: { ownerId: currentUser.$id },
    });

    // Initialize statistics object
    const totalSpace: any = {
      image: { size: 0, latestDate: "" },
      document: { size: 0, latestDate: "" },
      video: { size: 0, latestDate: "" },
      audio: { size: 0, latestDate: "" },
      other: { size: 0, latestDate: "" },
      used: 0,
      all: 2 * 1024 * 1024 * 1024, // 2GB available storage
    };

    files.forEach((file) => {
      const fileType = file.type;
      if (totalSpace[fileType] !== undefined) {
        totalSpace[fileType].size += file.size;
        totalSpace.used += file.size;

        const fileUpdatedAtStr = file.updatedAt.toISOString();
        if (
          !totalSpace[fileType].latestDate ||
          new Date(file.updatedAt) > new Date(totalSpace[fileType].latestDate)
        ) {
          totalSpace[fileType].latestDate = fileUpdatedAtStr;
        }
      }
    });

    return NextResponse.json(totalSpace);
  } catch (error) {
    console.error("Failed to calculate space usage:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
