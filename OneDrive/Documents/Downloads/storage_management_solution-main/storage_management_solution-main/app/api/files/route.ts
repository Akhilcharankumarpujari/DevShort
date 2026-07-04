import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { storageService } from "@/lib/services/storage";
import { getFileType } from "@/lib/utils";
import { getCurrentUser } from "@/lib/actions/user.actions";
import { mapFileToFrontend } from "@/lib/mappings";

// GET: List files for authenticated user
export async function GET(req: NextRequest) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const typesParam = searchParams.get("types"); // comma-separated
    const searchText = searchParams.get("searchText") || "";
    const sort = searchParams.get("sort") || "createdAt-desc";
    const limit = searchParams.get("limit") ? parseInt(searchParams.get("limit")!) : undefined;

    const types = typesParam ? typesParam.split(",") : [];

    // Parse sorting params
    const [sortByRaw, orderRaw] = (sort && sort.includes("-")) ? sort.split("-") : ["createdAt", "desc"];
    const sortBy = !sortByRaw || sortByRaw === "$createdAt" || sortByRaw === "createdAt" ? "createdAt" : sortByRaw;
    const orderBy = orderRaw === "asc" ? "asc" : "desc";

    // Setup base filters
    const whereClause: any = {
      OR: [
        { ownerId: currentUser.$id },
        { users: { has: currentUser.email } },
      ],
    };

    if (types.length > 0) {
      whereClause.type = { in: types };
    }

    if (searchText) {
      whereClause.name = { contains: searchText, mode: "insensitive" };
    }

    const files = await prisma.file.findMany({
      where: whereClause,
      orderBy: {
        [sortBy]: orderBy,
      },
      take: limit,
      include: {
        owner: true,
      },
    });

    const mappedFiles = files.map(mapFileToFrontend);

    return NextResponse.json({
      total: files.length,
      documents: mappedFiles,
    });
  } catch (error) {
    console.error("Failed to list files:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

// POST: Upload a file
export async function POST(req: NextRequest) {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const formData = await req.formData();
    const file = formData.get("file") as File;
    const ownerId = formData.get("ownerId") as string;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Convert file to buffer for upload
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    
    // Generate a unique storage key
    const uniqueId = Math.random().toString(36).substring(2, 15);
    const storageKey = `${uniqueId}-${file.name}`;
    
    // Upload to S3/MinIO
    await storageService.uploadFile(buffer, storageKey, file.type || "application/octet-stream");

    // Save metadata to database
    const fileTypeInfo = getFileType(file.name);
    const dbFile = await prisma.file.create({
      data: {
        name: file.name,
        originalName: file.name,
        type: fileTypeInfo.type,
        extension: fileTypeInfo.extension,
        size: file.size,
        storageKey,
        ownerId: ownerId || currentUser.$id,
      },
      include: {
        owner: true,
      },
    });

    return NextResponse.json(mapFileToFrontend(dbFile));
  } catch (error) {
    console.error("Failed to upload file:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
