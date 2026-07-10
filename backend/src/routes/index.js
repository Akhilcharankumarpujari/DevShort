import { Router } from "express";
import urlRoutes from "./url.routes.js";
import authRoutes from "./auth.routes.js";
import analyticsRoutes from "./analytics.routes.js";
import dashboardRoutes from "./dashboard.routes.js";

const router = Router();

// Auth routes first (before rate limiter in app.js applies to /api/urls)
router.use(authRoutes);

// Analytics & dashboard routes
router.use(analyticsRoutes);
router.use(dashboardRoutes);

// URL routes (includes redirect at /:shortCode)
router.use(urlRoutes);

export default router;
