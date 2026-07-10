import crypto from "crypto";

/**
 * Simple User-Agent parser.
 * Returns { browser, browserVersion, os, deviceType }
 */
export function parseUserAgent(uaString) {
  if (!uaString) {
    return { browser: "Unknown", browserVersion: "", os: "Unknown", deviceType: "desktop" };
  }

  const ua = uaString;
  let browser = "Unknown";
  let browserVersion = "";
  let os = "Unknown";
  let deviceType = "desktop";

  // --- Browser detection ---
  if (ua.includes("Edg/")) {
    browser = "Edge";
    browserVersion = (ua.match(/Edg\/([\d.]+)/) || [])[1] || "";
  } else if (ua.includes("OPR/") || ua.includes("Opera/")) {
    browser = "Opera";
    browserVersion = (ua.match(/OPR\/([\d.]+)/) || ua.match(/Opera\/([\d.]+)/) || [])[1] || "";
  } else if (ua.includes("Chrome/") && !ua.includes("Edg/")) {
    browser = "Chrome";
    browserVersion = (ua.match(/Chrome\/([\d.]+)/) || [])[1] || "";
  } else if (ua.includes("Safari/") && !ua.includes("Chrome/")) {
    browser = "Safari";
    browserVersion = (ua.match(/Version\/([\d.]+)/) || [])[1] || "";
  } else if (ua.includes("Firefox/")) {
    browser = "Firefox";
    browserVersion = (ua.match(/Firefox\/([\d.]+)/) || [])[1] || "";
  }

  // --- OS detection ---
  if (ua.includes("Windows")) {
    os = "Windows";
  } else if (ua.includes("Mac OS") || ua.includes("Macintosh")) {
    os = "macOS";
  } else if (ua.includes("Linux") && !ua.includes("Android")) {
    os = "Linux";
  } else if (ua.includes("Android")) {
    os = "Android";
  } else if (ua.includes("iPhone") || ua.includes("iPad") || ua.includes("iOS")) {
    os = "iOS";
  }

  // --- Device type ---
  if (ua.includes("Mobile") || ua.includes("Android") && ua.includes("Mobile")) {
    deviceType = "mobile";
  } else if (ua.includes("Tablet") || ua.includes("iPad")) {
    deviceType = "tablet";
  }

  return { browser, browserVersion, os, deviceType };
}

/**
 * Hash an IP address with SHA-256 for privacy.
 */
export function hashIP(ip) {
  if (!ip) return null;
  // Extract the first IP if there are multiple (proxies)
  const firstIP = ip.split(",")[0].trim();
  return crypto.createHash("sha256").update(firstIP).digest("hex").slice(0, 16);
}

/**
 * Extract country from Accept-Language header (best-effort).
 */
export function detectCountry(acceptLanguage) {
  if (!acceptLanguage) return null;
  // Simple mapping of common language tags to country codes
  const first = acceptLanguage.split(",")[0].trim();
  const parts = first.split("-");
  if (parts.length > 1) {
    return parts[parts.length - 1].toUpperCase();
  }
  return null;
}
