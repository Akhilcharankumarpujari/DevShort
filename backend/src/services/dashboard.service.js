import prisma from "../lib/prisma.js";
import config from "../config/index.js";

export async function getUserDashboard(userId, options = {}) {
  const {
    page = 1,
    limit = 10,
    search = "",
    sortBy = "createdAt",
    sortOrder = "desc",
  } = options;

  const skip = (page - 1) * limit;
  const take = limit;

  // Build where clause
  const where = { userId };

  if (search) {
    where.OR = [
      { originalUrl: { contains: search, mode: "insensitive" } },
      { shortCode: { contains: search, mode: "insensitive" } },
      { customAlias: { contains: search, mode: "insensitive" } },
    ];
  }

  // Build orderBy
  const orderBy = {};
  const allowedSortFields = ["createdAt", "clickCount", "lastClicked", "originalUrl"];
  const field = allowedSortFields.includes(sortBy) ? sortBy : "createdAt";
  orderBy[field] = sortOrder === "asc" ? "asc" : "desc";

  // Fetch URLs with count
  const [urls, total] = await Promise.all([
    prisma.url.findMany({
      where,
      skip,
      take,
      orderBy,
    }),
    prisma.url.count({ where }),
  ]);

  const totalClicks = await prisma.url.aggregate({
    where: { userId },
    _sum: { clickCount: true },
  });

  const urlsWithShortUrl = urls.map((url) => ({
    ...url,
    shortUrl: `${config.baseUrl}/${url.shortCode}`,
  }));

  return {
    urls: urlsWithShortUrl,
    pagination: {
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    },
    totalClicks: totalClicks._sum.clickCount || 0,
  };
}
