import { Router } from "express";
import analyticsController from "../controllers/analytics.controller.js";
import { authenticate } from "../middleware/auth.js";

const router = Router();

router.get("/api/analytics/overview", authenticate, analyticsController.getOverview);

export default router;
