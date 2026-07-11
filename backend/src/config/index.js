// CORS_ORIGIN may be a comma-separated list of allowed origins.
// e.g. "http://18.210.143.141:5173,http://localhost:5173,http://localhost:3000"
const parseCorsOrigins = (raw) => {
  const fallback = ["http://localhost:5173"];
  if (!raw) return fallback;
  return raw.split(",").map((o) => o.trim()).filter(Boolean);
};

const config = Object.freeze({
  port: parseInt(process.env.PORT, 10) || 4000,
  nodeEnv: process.env.NODE_ENV || "development",
  databaseUrl: process.env.DATABASE_URL,
  shortCodeLength: parseInt(process.env.SHORT_CODE_LENGTH, 10) || 8,
  baseUrl: process.env.BASE_URL || "http://localhost:4000",
  corsOrigins: parseCorsOrigins(process.env.CORS_ORIGIN),
  jwtSecret: process.env.JWT_SECRET || "devshort-dev-secret-change-in-production",
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || "7d",
});

if (!config.databaseUrl) {
  throw new Error("DATABASE_URL environment variable is required");
}

export default config;
