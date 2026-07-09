const config = Object.freeze({
  port: parseInt(process.env.PORT, 10) || 4000,
  nodeEnv: process.env.NODE_ENV || "development",
  databaseUrl: process.env.DATABASE_URL,
  shortCodeLength: parseInt(process.env.SHORT_CODE_LENGTH, 10) || 8,
  baseUrl: process.env.BASE_URL || "http://localhost:4000",
  corsOrigin: process.env.CORS_ORIGIN || "http://localhost:5173",
});

if (!config.databaseUrl) {
  throw new Error("DATABASE_URL environment variable is required");
}

export default config;
