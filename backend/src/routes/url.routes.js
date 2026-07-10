import { Router } from "express";
import urlController from "../controllers/url.controller.js";
import validateUrl from "../middleware/validateUrl.js";
import { authenticate, optionalAuth } from "../middleware/auth.js";

const router = Router();

// Public: shorten URL (optional auth for user association)
router.post("/api/urls", optionalAuth, validateUrl, urlController.shortenUrl);

// Public/semi-public: list URLs
router.get("/api/urls", optionalAuth, urlController.listUrls);

// Protected: get single URL detail
router.get("/api/urls/:id", authenticate, urlController.getUrl);

// Protected: update URL
router.patch("/api/urls/:id", authenticate, urlController.updateUrl);

// Protected: delete URL
router.delete("/api/urls/:id", authenticate, urlController.deleteUrl);

// Protected: get URL analytics
router.get("/api/urls/:id/analytics", authenticate, urlController.getUrlAnalytics);

// Health check
router.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Public: redirect (MUST be last to not catch /api/* routes)
router.get("/:shortCode", urlController.redirectUrl);

export default router;
