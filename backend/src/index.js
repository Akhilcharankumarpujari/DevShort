import app from "./app.js";
import config from "./config/index.js";
import prisma from "./lib/prisma.js";

async function main() {
  await prisma.$connect();
  console.log("Connected to PostgreSQL");

  const server = app.listen(config.port, () => {
    console.log(`Server running on port ${config.port}`);
  });

  const shutdown = async (signal) => {
    console.log(`\n${signal} received. Shutting down gracefully...`);
    server.close(async () => {
      await prisma.$disconnect();
      console.log("Disconnected from PostgreSQL");
      process.exit(0);
    });

    setTimeout(() => {
      console.error("Forced shutdown after timeout");
      process.exit(1);
    }, 10000);
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
