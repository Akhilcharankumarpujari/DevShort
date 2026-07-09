import urlService from "../services/url.service.js";

async function shortenUrl(req, res, next) {
  try {
    const { url } = req.body;
    const result = await urlService.createUrl(url);

    res.status(201).json({
      data: {
        id: result.id,
        originalUrl: result.originalUrl,
        shortCode: result.shortCode,
        shortUrl: result.shortUrl,
        clickCount: result.clickCount,
        createdAt: result.createdAt,
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

    await urlService.incrementClickCount(url.id);

    res.redirect(302, url.originalUrl);
  } catch (error) {
    next(error);
  }
}

async function listUrls(_req, res, next) {
  try {
    const urls = await urlService.getAllUrls();
    res.json({ data: urls });
  } catch (error) {
    next(error);
  }
}

export default { shortenUrl, redirectUrl, listUrls };
