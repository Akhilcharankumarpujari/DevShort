import { Router } from "express";
import dashboardController from "../controllers/dashboard.controller.js";
import { authenticate } from "../middleware/auth.js";

const router = Router();

router.get("/api/dashboard", authenticate, dashboardController.getDashboard);

export default router;
