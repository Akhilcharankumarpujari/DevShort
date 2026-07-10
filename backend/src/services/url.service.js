import prisma from "../lib/prisma.js";
import config from "../config/index.js";
import { generateShortCode } from "../utils/nanoid.js";
import { NotFoundError, ConflictError, ForbiddenError } from "../utils/apiError.js";
import { parseUserAgent, hashIP, detectCountry } from "../utils/analytics.js";

const MAX_COLLISION_RETRIES = 3;
const CUSTOM_ALIAS_REGEX = /^[a-zA-Z0-9_-]{4,30}$/;

async function createUrl(originalUrl, options = {}) {
  const { userId = null, customAlias = null, expiresAt = null } = options;

  // If custom alias provided, validate and use it
  if (customAlias) {
    if (!CUSTOM_ALIAS_REGEX.test(customAlias)) {
      throw new ConflictError(
        "Custom alias must be 4-30 characters using letters, numbers, hyphens, and underscores"
      );
    }

    // Check if custom alias is already taken
    const existing = await prisma.url.findFirst({
      where: {
        OR: [{ shortCode: customAlias }, { customAlias: customAlias }],
      },
    });

    if (existing) {
      throw new ConflictError("This custom alias is already taken");
    }

    const url = await prisma.url.create({
      data: {
        originalUrl,
        shortCode: customAlias,
        customAlias,
        expiresAt: expiresAt ? new Date(expiresAt) : null,
        userId,
      },
    });

    return { ...url, shortUrl: `${config.baseUrl}/${url.shortCode}` };
  }

  // Auto-generate short code with collision retry
  for (let attempt = 0; attempt < MAX_COLLISION_RETRIES; attempt++) {
    const shortCode = generateShortCode();

    try {
      const url = await prisma.url.create({
        data: {
          originalUrl,
          shortCode,
          expiresAt: expiresAt ? new Date(expiresAt) : null,
          userId,
        },
      });

      return { ...url, shortUrl: `${config.baseUrl}/${url.shortCode}` };
    } catch (error) {
      if (error.code === "P2002" && attempt < MAX_COLLISION_RETRIES - 1) {
        continue;
      }
      if (error.code === "P2002") {
        throw new ConflictError("Short code collision, please try again");
      }
      throw error;
    }
  }
}

async function getUrlByShortCode(shortCode) {
  const url = await prisma.url.findUnique({ where: { shortCode } });

  if (!url) {
    throw new NotFoundError("URL not found");
  }

  // Check expiration
  if (url.expiresAt && new Date() > url.expiresAt) {
    throw new NotFoundError("This link has expired");
  }

  return url;
}

async function getUrlById(id, userId = null) {
  const url = await prisma.url.findUnique({ where: { id } });

  if (!url) {
    throw new NotFoundError("URL not found");
  }

  // Only the owner can view the full details
  if (userId && url.userId && url.userId !== userId) {
    throw new ForbiddenError("You do not have permission to view this URL");
  }

  return { ...url, shortUrl: `${config.baseUrl}/${url.shortCode}` };
}

async function updateUrl(id, userId, data) {
  const url = await prisma.url.findUnique({ where: { id } });

  if (!url) {
    throw new NotFoundError("URL not found");
  }

  if (url.userId && url.userId !== userId) {
    throw new ForbiddenError("You do not have permission to edit this URL");
  }

  const updateData = {};

  if (data.originalUrl !== undefined) {
    updateData.originalUrl = data.originalUrl;
  }

  if (data.customAlias !== undefined) {
    if (!CUSTOM_ALIAS_REGEX.test(data.customAlias)) {
      throw new ConflictError(
        "Custom alias must be 4-30 characters using letters, numbers, hyphens, and underscores"
      );
    }

    // Check uniqueness
    const existing = await prisma.url.findFirst({
      where: {
        OR: [{ shortCode: data.customAlias }, { customAlias: data.customAlias }],
        NOT: { id },
      },
    });

    if (existing) {
      throw new ConflictError("This custom alias is already taken");
    }

    updateData.customAlias = data.customAlias;
    updateData.shortCode = data.customAlias;
  }

  if (data.expiresAt !== undefined) {
    updateData.expiresAt = data.expiresAt ? new Date(data.expiresAt) : null;
  }

  const updated = await prisma.url.update({
    where: { id },
    data: updateData,
  });

  return { ...updated, shortUrl: `${config.baseUrl}/${updated.shortCode}` };
}

async function deleteUrl(id, userId) {
  const url = await prisma.url.findUnique({ where: { id } });

  if (!url) {
    throw new NotFoundError("URL not found");
  }

  if (url.userId && url.userId !== userId) {
    throw new ForbiddenError("You do not have permission to delete this URL");
  }

  await prisma.url.delete({ where: { id } });

  return { message: "URL deleted successfully" };
}

async function incrementClickCount(id) {
  await prisma.url.update({
    where: { id },
    data: {
      clickCount: { increment: 1 },
      lastClicked: new Date(),
    },
  });
}

async function recordClickEvent(urlId, req) {
  try {
    const userAgent = req.headers["user-agent"] || "";
    const ip =
      req.headers["x-forwarded-for"] || req.ip || req.connection?.remoteAddress || "";
    const referrer = req.headers.referer || req.headers.referrer || "";
    const acceptLanguage = req.headers["accept-language"] || "";

    const { browser, browserVersion, os, deviceType } = parseUserAgent(userAgent);
    const ipHash = hashIP(ip);
    const country = detectCountry(acceptLanguage);

    await prisma.clickEvent.create({
      data: {
        urlId,
        browser,
        browserVersion,
        os,
        deviceType,
        country,
        referrer: referrer ? referrer.slice(0, 500) : null,
        ipHash,
      },
    });
  } catch (error) {
    // Analytics recording failure should never break the redirect
    console.error("Failed to record click event:", error.message);
  }
}

async function getAllUrls(userId = null) {
  const where = userId ? { userId } : {};

  const urls = await prisma.url.findMany({
    where,
    orderBy: { createdAt: "desc" },
    take: 50,
  });

  return urls.map((url) => ({
    ...url,
    shortUrl: `${config.baseUrl}/${url.shortCode}`,
  }));
}

export default {
  createUrl,
  getUrlByShortCode,
  getUrlById,
  updateUrl,
  deleteUrl,
  incrementClickCount,
  recordClickEvent,
  getAllUrls,
};
