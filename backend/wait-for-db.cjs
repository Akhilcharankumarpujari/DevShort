// CommonJS script to wait for PostgreSQL using PrismaClient
const { PrismaClient } = require('@prisma/client');

async function main() {
  const prisma = new PrismaClient();
  try {
    await prisma.$connect();
    console.log('DB ready');
    await prisma.$disconnect();
    process.exit(0);
  } catch (e) {
    console.error('DB not ready:', e.message);
    await prisma.$disconnect();
    process.exit(1);
  }
}

main();
