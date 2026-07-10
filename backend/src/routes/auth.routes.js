import { Router } from "express";
import authController from "../controllers/auth.controller.js";
import { authenticate } from "../middleware/auth.js";

const router = Router();

router.post("/api/auth/register", authController.register);
router.post("/api/auth/login", authController.login);
router.get("/api/auth/me", authenticate, authController.me);

export default router;
