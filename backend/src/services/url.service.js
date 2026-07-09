import prisma from "../lib/prisma.js";
import config from "../config/index.js";
import { generateShortCode } from "../utils/nanoid.js";
import { NotFoundError, ConflictError } from "../utils/apiError.js";

const MAX_COLLISION_RETRIES = 3;

async function createUrl(originalUrl) {
  for (let attempt = 0; attempt < MAX_COLLISION_RETRIES; attempt++) {
    const shortCode = generateShortCode();

    try {
      const url = await prisma.url.create({
        data: { originalUrl, shortCode },
      });

      return {
        ...url,
        shortUrl: `${config.baseUrl}/${url.shortCode}`,
      };
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

  return url;
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

async function getAllUrls() {
  const urls = await prisma.url.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
  });

  return urls.map((url) => ({
    ...url,
    shortUrl: `${config.baseUrl}/${url.shortCode}`,
  }));
}

export default { createUrl, getUrlByShortCode, incrementClickCount, getAllUrls };
