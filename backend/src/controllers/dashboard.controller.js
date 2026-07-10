import dashboardService from "../services/dashboard.service.js";

async function getDashboard(req, res, next) {
  try {
    const userId = req.user.id;
    const { page, limit, search, sortBy, sortOrder } = req.query;

    const result = await dashboardService.getUserDashboard(userId, {
      page: parseInt(page, 10) || 1,
      limit: Math.min(parseInt(limit, 10) || 10, 50),
      search: search || "",
      sortBy: sortBy || "createdAt",
      sortOrder: sortOrder || "desc",
    });

    res.json({ data: result });
  } catch (error) {
    next(error);
  }
}

export default { getDashboard };
