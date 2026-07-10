import analyticsService from "../services/analytics.service.js";

async function getOverview(req, res, next) {
  try {
    const userId = req.user.id;
    const analytics = await analyticsService.getAggregateAnalytics(userId);
    res.json({ data: analytics });
  } catch (error) {
    next(error);
  }
}

export default { getOverview };
