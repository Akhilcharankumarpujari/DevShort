import { prisma } from "@/lib/prisma";
import { getCurrentUser, revalidatePathAction } from "./user.actions";
import { mapFileToFrontend } from "@/lib/mappings";

/**
 * Uploads a file via client-side fetch to the /api/files route
 */
export const uploadFile = async ({
  file,
  ownerId,
  accountId,
  path,
}: UploadFileProps) => {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("ownerId", ownerId);
    formData.append("accountId", accountId);

    const response = await fetch("/api/files", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Failed to upload file");
    const data = await response.json();

    // Revalidate dashboard/list view cache
    await revalidatePathAction(path);
    return data;
  } catch (error) {
    console.error("Error in uploadFile action:", error);
    return null;
  }
};

/**
 * Lists files. Executed server-side within Server Components
 */
export const getFiles = async ({
  types = [],
  searchText = "",
  sort = "$createdAt-desc",
  limit,
}: GetFilesProps) => {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) throw new Error("User not found");

    // Parse sorting fields
    const [sortByRaw, orderRaw] = (sort && sort.includes("-")) ? sort.split("-") : ["createdAt", "desc"];
    const sortBy =
      !sortByRaw || sortByRaw === "$createdAt" || sortByRaw === "createdAt"
        ? "createdAt"
        : sortByRaw;
    const orderBy = orderRaw === "asc" ? "asc" : "desc";

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

    return {
      total: files.length,
      documents: files.map(mapFileToFrontend),
    };
  } catch (error) {
    console.error("Error in getFiles action:", error);
    return { total: 0, documents: [] };
  }
};

/**
 * Renames a file via client-side fetch to /api/files/[id] (PATCH)
 */
export const renameFile = async ({
  fileId,
  name,
  extension,
  path,
}: RenameFileProps) => {
  try {
    const response = await fetch(`/api/files/${fileId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name: `${name}.${extension}` }),
    });

    if (!response.ok) throw new Error("Failed to rename file");
    const data = await response.json();

    await revalidatePathAction(path);
    return data;
  } catch (error) {
    console.error("Error in renameFile action:", error);
    return null;
  }
};

/**
 * Updates shared file user list via client-side fetch to /api/files/[id]/share (POST)
 */
export const updateFileUsers = async ({
  fileId,
  emails,
  path,
}: UpdateFileUsersProps) => {
  try {
    const response = await fetch(`/api/files/${fileId}/share`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ emails }),
    });

    if (!response.ok) throw new Error("Failed to share file");
    const data = await response.json();

    await revalidatePathAction(path);
    return data;
  } catch (error) {
    console.error("Error in updateFileUsers action:", error);
    return null;
  }
};

/**
 * Deletes a file via client-side fetch to /api/files/[id] (DELETE)
 */
export const deleteFile = async ({
  fileId,
  bucketFileId, // kept for backward compatibility (maps to storageKey)
  path,
}: DeleteFileProps) => {
  try {
    const response = await fetch(`/api/files/${fileId}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error("Failed to delete file");
    const data = await response.json();

    await revalidatePathAction(path);
    return data;
  } catch (error) {
    console.error("Error in deleteFile action:", error);
    return null;
  }
};

/**
 * Calculates total storage space used. Executed server-side in Server Components
 */
export const getTotalSpaceUsed = async () => {
  try {
    const currentUser = await getCurrentUser();
    if (!currentUser) throw new Error("User is not authenticated.");

    const files = await prisma.file.findMany({
      where: { ownerId: currentUser.$id },
    });

    const totalSpace: any = {
      image: { size: 0, latestDate: "" },
      document: { size: 0, latestDate: "" },
      video: { size: 0, latestDate: "" },
      audio: { size: 0, latestDate: "" },
      other: { size: 0, latestDate: "" },
      used: 0,
      all: 2 * 1024 * 1024 * 1024, // 2GB total storage allocation
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

    return totalSpace;
  } catch (error) {
    console.error("Error in getTotalSpaceUsed:", error);
    return {
      image: { size: 0, latestDate: "" },
      document: { size: 0, latestDate: "" },
      video: { size: 0, latestDate: "" },
      audio: { size: 0, latestDate: "" },
      other: { size: 0, latestDate: "" },
      used: 0,
      all: 2 * 1024 * 1024 * 1024,
    };
  }
};
