/**
 * Maps database file object to frontend compatible Appwrite Model.Document format
 */
export function mapFileToFrontend(file: any) {
  return {
    $id: file.id,
    $createdAt: file.createdAt.toISOString(),
    $updatedAt: file.updatedAt.toISOString(),
    name: file.name,
    originalName: file.originalName,
    size: file.size,
    type: file.type,
    extension: file.extension,
    storageKey: file.storageKey,
    bucketFileId: file.storageKey, // backward compatibility
    url: `/api/files/${file.id}/view`,
    owner: {
      $id: file.owner.id,
      fullName: file.owner.fullName,
      email: file.owner.email,
      avatar: file.owner.avatar || "",
    },
    users: file.users || [],
  };
}
