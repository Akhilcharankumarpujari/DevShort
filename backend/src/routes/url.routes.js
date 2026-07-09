import { Router } from "express";
import urlController from "../controllers/url.controller.js";
import validateUrl from "../middleware/validateUrl.js";

const router = Router();

router.post("/api/urls", validateUrl, urlController.shortenUrl);

router.get("/api/urls", urlController.listUrls);

router.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

router.get("/:shortCode", urlController.redirectUrl);

export default router;
