import prisma from "../lib/prisma.js";

export async function getUrlAnalytics(urlId) {
  const url = await prisma.url.findUnique({
    where: { id: urlId },
    select: {
      id: true,
      originalUrl: true,
      shortCode: true,
      clickCount: true,
      createdAt: true,
    },
  });

  if (!url) return null;

  // Total events
  const totalEvents = await prisma.clickEvent.count({ where: { urlId } });

  // Browser stats
  const browserStats = await prisma.clickEvent.groupBy({
    by: ["browser"],
    where: { urlId },
    _count: { browser: true },
    orderBy: { _count: { browser: "desc" } },
  });

  // Device stats
  const deviceStats = await prisma.clickEvent.groupBy({
    by: ["deviceType"],
    where: { urlId },
    _count: { deviceType: true },
    orderBy: { _count: { deviceType: "desc" } },
  });

  // OS stats
  const osStats = await prisma.clickEvent.groupBy({
    by: ["os"],
    where: { urlId },
    _count: { os: true },
    orderBy: { _count: { os: "desc" } },
  });

  // Country stats
  const countryStats = await prisma.clickEvent.groupBy({
    by: ["country"],
    where: { urlId, country: { not: null } },
    _count: { country: true },
    orderBy: { _count: { country: "desc" } },
    take: 10,
  });

  // Referrer stats
  const referrerStats = await prisma.clickEvent.groupBy({
    by: ["referrer"],
    where: { urlId, referrer: { not: null } },
    _count: { referrer: true },
    orderBy: { _count: { referrer: "desc" } },
    take: 10,
  });

  // Daily clicks for last 30 days
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const dailyClicks = await prisma.clickEvent.findMany({
    where: { urlId, timestamp: { gte: thirtyDaysAgo } },
    select: { timestamp: true },
    orderBy: { timestamp: "asc" },
  });

  // Aggregate by day
  const dailyMap = {};
  dailyClicks.forEach((event) => {
    const day = event.timestamp.toISOString().slice(0, 10);
    dailyMap[day] = (dailyMap[day] || 0) + 1;
  });

  const dailyData = Object.entries(dailyMap)
    .map(([date, clicks]) => ({ date, clicks }))
    .sort((a, b) => a.date.localeCompare(b.date));

  return {
    url: {
      id: url.id,
      originalUrl: url.originalUrl,
      shortCode: url.shortCode,
      clickCount: url.clickCount,
      createdAt: url.createdAt,
    },
    totalEvents,
    browserStats: browserStats.map((b) => ({
      browser: b.browser || "Unknown",
      count: b._count.browser,
    })),
    deviceStats: deviceStats.map((d) => ({
      deviceType: d.deviceType || "Unknown",
      count: d._count.deviceType,
    })),
    osStats: osStats.map((o) => ({
      os: o.os || "Unknown",
      count: o._count.os,
    })),
    countryStats: countryStats.map((c) => ({
      country: c.country || "Unknown",
      count: c._count.country,
    })),
    referrerStats: referrerStats.map((r) => ({
      referrer: r.referrer || "Direct",
      count: r._count.referrer,
    })),
    dailyClicks: dailyData,
  };
}

export async function getAggregateAnalytics(userId) {
  const urls = await prisma.url.findMany({
    where: { userId },
    select: {
      id: true,
      originalUrl: true,
      shortCode: true,
      clickCount: true,
      createdAt: true,
      lastClicked: true,
      expiresAt: true,
    },
    orderBy: { clickCount: "desc" },
  });

  const totalUrls = urls.length;
  const totalClicks = urls.reduce((sum, u) => sum + u.clickCount, 0);
  const activeLinks = urls.filter((u) => !u.expiresAt || new Date() <= u.expiresAt).length;

  // Aggregate daily clicks across all user URLs
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const urlIds = urls.map((u) => u.id);

  const dailyClicks = await prisma.clickEvent.findMany({
    where: {
      urlId: { in: urlIds },
      timestamp: { gte: thirtyDaysAgo },
    },
    select: { timestamp: true },
    orderBy: { timestamp: "asc" },
  });

  const dailyMap = {};
  dailyClicks.forEach((event) => {
    const day = event.timestamp.toISOString().slice(0, 10);
    dailyMap[day] = (dailyMap[day] || 0) + 1;
  });

  const dailyData = Object.entries(dailyMap)
    .map(([date, clicks]) => ({ date, clicks }))
    .sort((a, b) => a.date.localeCompare(b.date));

  // Browser stats across all URLs
  const browserStats = await prisma.clickEvent.groupBy({
    by: ["browser"],
    where: { urlId: { in: urlIds } },
    _count: { browser: true },
    orderBy: { _count: { browser: "desc" } },
  });

  // Device stats
  const deviceStats = await prisma.clickEvent.groupBy({
    by: ["deviceType"],
    where: { urlId: { in: urlIds } },
    _count: { deviceType: true },
    orderBy: { _count: { deviceType: "desc" } },
  });

  // Top URLs
  const topUrls = urls.slice(0, 10).map((u) => ({
    id: u.id,
    originalUrl: u.originalUrl,
    shortCode: u.shortCode,
    clickCount: u.clickCount,
    createdAt: u.createdAt,
    lastClicked: u.lastClicked,
  }));

  return {
    overview: {
      totalUrls,
      totalClicks,
      activeLinks,
    },
    topUrls,
    dailyClicks: dailyData,
    browserStats: browserStats.map((b) => ({
      browser: b.browser || "Unknown",
      count: b._count.browser,
    })),
    deviceStats: deviceStats.map((d) => ({
      deviceType: d.deviceType || "Unknown",
      count: d._count.deviceType,
    })),
  };
}

export default {
  getUrlAnalytics,
  getAggregateAnalytics,
};

