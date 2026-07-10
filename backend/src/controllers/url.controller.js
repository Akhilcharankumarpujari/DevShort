import urlService from "../services/url.service.js";
import analyticsService from "../services/analytics.service.js";

async function shortenUrl(req, res, next) {
  try {
    const { url, customAlias, expiresAt } = req.body;
    const userId = req.user?.id || null;

    const result = await urlService.createUrl(url, {
      userId,
      customAlias: customAlias || null,
      expiresAt: expiresAt || null,
    });

    res.status(201).json({
      data: {
        id: result.id,
        originalUrl: result.originalUrl,
        shortCode: result.shortCode,
        shortUrl: result.shortUrl,
        customAlias: result.customAlias,
        clickCount: result.clickCount,
        createdAt: result.createdAt,
        expiresAt: result.expiresAt,
        lastClickedAt: result.lastClicked,
      },
    });
  } catch (error) {
    next(error);
  }
}

async function redirectUrl(req, res, next) {
  try {
    const { shortCode } = req.params;
    const url = await urlService.getUrlByShortCode(shortCode);

    // Increment click count
    await urlService.incrementClickCount(url.id);

    // Fire-and-forget analytics recording
    urlService.recordClickEvent(url.id, req).catch((err) => {
      console.error("Analytics recording failed:", err.message);
    });

    res.redirect(302, url.originalUrl);
  } catch (error) {
    next(error);
  }
}

async function listUrls(req, res, next) {
  try {
    const userId = req.user?.id || null;
    const urls = await urlService.getAllUrls(userId);
    res.json({ data: urls });
  } catch (error) {
    next(error);
  }
}

async function getUrl(req, res, next) {
  try {
    const { id } = req.params;
    const userId = req.user?.id || null;
    const url = await urlService.getUrlById(id, userId);
    res.json({ data: url });
  } catch (error) {
    next(error);
  }
}

async function updateUrl(req, res, next) {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const { originalUrl, customAlias, expiresAt } = req.body;

    const url = await urlService.updateUrl(id, userId, {
      originalUrl,
      customAlias,
      expiresAt,
    });

    res.json({ data: url });
  } catch (error) {
    next(error);
  }
}

async function deleteUrl(req, res, next) {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const result = await urlService.deleteUrl(id, userId);
    res.json({ data: result });
  } catch (error) {
    next(error);
  }
}

async function getUrlAnalytics(req, res, next) {
  try {
    const { id } = req.params;
    const userId = req.user.id;

    // Verify ownership first
    const url = await urlService.getUrlById(id, userId);

    const analytics = await analyticsService.getUrlAnalytics(url.id);

    if (!analytics) {
      return res.status(404).json({
        error: { message: "URL not found", status: 404 },
      });
    }

    res.json({ data: analytics });
  } catch (error) {
    next(error);
  }
}

export default {
  shortenUrl,
  redirectUrl,
  listUrls,
  getUrl,
  updateUrl,
  deleteUrl,
  getUrlAnalytics,
};
