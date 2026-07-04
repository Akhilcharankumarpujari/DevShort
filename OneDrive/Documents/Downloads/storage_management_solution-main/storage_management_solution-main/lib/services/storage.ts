import {
  S3Client,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand,
  CopyObjectCommand,
} from "@aws-sdk/client-s3";
import fs from "fs";
import path from "path";
import { Readable } from "stream";

const s3Client = new S3Client({
  endpoint: process.env.S3_ENDPOINT,
  region: process.env.S3_REGION || "us-east-1",
  credentials: {
    accessKeyId: process.env.S3_ACCESS_KEY || "",
    secretAccessKey: process.env.S3_SECRET_KEY || "",
  },
  forcePathStyle: process.env.S3_FORCE_PATH_STYLE === "true",
});

const BUCKET_NAME = process.env.S3_BUCKET || "zidoc";

// Local storage paths
const UPLOADS_DIR = path.join(process.cwd(), "public", "uploads");

// Helper to ensure local uploads directory exists
function ensureUploadsDir() {
  if (!fs.existsSync(UPLOADS_DIR)) {
    fs.mkdirSync(UPLOADS_DIR, { recursive: true });
  }
}

// Helper to determine if we should fallback to local storage on error
function isConnectionError(error: any): boolean {
  const code = error?.code || "";
  const message = error?.message || "";
  return (
    code === "ECONNREFUSED" ||
    code === "ENOTFOUND" ||
    code === "ETIMEDOUT" ||
    message.includes("connect ECONNREFUSED") ||
    message.includes("UnknownEndpoint")
  );
}

// Local storage service fallback implementation
const localStorageService = {
  async uploadFile(fileBuffer: Buffer, key: string): Promise<string> {
    ensureUploadsDir();
    const filePath = path.join(UPLOADS_DIR, key);
    await fs.promises.writeFile(filePath, fileBuffer);
    return key;
  },

  async getFileStream(key: string) {
    ensureUploadsDir();
    const filePath = path.join(UPLOADS_DIR, key);
    if (!fs.existsSync(filePath)) {
      throw new Error("File not found locally");
    }

    const fileBuffer = await fs.promises.readFile(filePath);
    // Mimic the S3 GetObjectCommand response structure
    return {
      Body: Readable.from(fileBuffer),
      ContentType: getMimeType(key),
      ContentLength: fileBuffer.length,
    };
  },

  async deleteFile(key: string): Promise<void> {
    ensureUploadsDir();
    const filePath = path.join(UPLOADS_DIR, key);
    if (fs.existsSync(filePath)) {
      await fs.promises.unlink(filePath);
    }
  },

  async renameFile(oldKey: string, newKey: string): Promise<string> {
    ensureUploadsDir();
    const oldPath = path.join(UPLOADS_DIR, oldKey);
    const newPath = path.join(UPLOADS_DIR, newKey);
    if (fs.existsSync(oldPath)) {
      await fs.promises.rename(oldPath, newPath);
    }
    return newKey;
  },
};

// Helper to guess mime type from file extension
function getMimeType(filename: string): string {
  const ext = path.extname(filename).toLowerCase();
  switch (ext) {
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".png":
      return "image/png";
    case ".gif":
      return "image/gif";
    case ".svg":
      return "image/svg+xml";
    case ".pdf":
      return "application/pdf";
    case ".txt":
      return "text/plain";
    case ".mp4":
      return "video/mp4";
    case ".mp3":
      return "audio/mpeg";
    default:
      return "application/octet-stream";
  }
}

export const storageService = {
  /**
   * Uploads a file buffer to S3/MinIO (falls back to local filesystem if S3 is unavailable)
   */
  async uploadFile(fileBuffer: Buffer, key: string, contentType: string): Promise<string> {
    try {
      const command = new PutObjectCommand({
        Bucket: BUCKET_NAME,
        Key: key,
        Body: fileBuffer,
        ContentType: contentType,
      });
      await s3Client.send(command);
      return key;
    } catch (error: any) {
      if (isConnectionError(error)) {
        console.warn("S3/MinIO connection refused. Falling back to local storage.");
        return localStorageService.uploadFile(fileBuffer, key);
      }
      throw error;
    }
  },

  /**
   * Retrieves a file object (falls back to local filesystem if S3 is unavailable)
   */
  async getFileStream(key: string) {
    try {
      const command = new GetObjectCommand({
        Bucket: BUCKET_NAME,
        Key: key,
      });
      const response = await s3Client.send(command);
      return response;
    } catch (error: any) {
      if (isConnectionError(error) || error?.name === "NoSuchKey") {
        console.warn("S3/MinIO unavailable or file not found. Trying local storage.");
        return localStorageService.getFileStream(key);
      }
      throw error;
    }
  },

  /**
   * Deletes a file (falls back to local filesystem if S3 is unavailable)
   */
  async deleteFile(key: string): Promise<void> {
    try {
      const command = new DeleteObjectCommand({
        Bucket: BUCKET_NAME,
        Key: key,
      });
      await s3Client.send(command);
    } catch (error: any) {
      if (isConnectionError(error)) {
        console.warn("S3/MinIO connection refused. Falling back to local storage delete.");
        return localStorageService.deleteFile(key);
      }
      throw error;
    }
  },

  /**
   * Renames a file (falls back to local filesystem if S3 is unavailable)
   */
  async renameFile(oldKey: string, newKey: string): Promise<string> {
    try {
      const copyCommand = new CopyObjectCommand({
        Bucket: BUCKET_NAME,
        CopySource: encodeURIComponent(`${BUCKET_NAME}/${oldKey}`),
        Key: newKey,
      });
      await s3Client.send(copyCommand);

      const deleteCommand = new DeleteObjectCommand({
        Bucket: BUCKET_NAME,
        Key: oldKey,
      });
      await s3Client.send(deleteCommand);

      return newKey;
    } catch (error: any) {
      if (isConnectionError(error)) {
        console.warn("S3/MinIO connection refused. Falling back to local storage rename.");
        return localStorageService.renameFile(oldKey, newKey);
      }
      throw error;
    }
  },
};
