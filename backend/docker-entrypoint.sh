#!/bin/sh
set -e

echo "==> Waiting for PostgreSQL to be ready..."
until node /app/wait-for-db.cjs 2>/dev/null; do
  echo "    PostgreSQL is unavailable - sleeping 2s"
  sleep 2
done

echo "==> Running Prisma db push..."
prisma db push --skip-generate --accept-data-loss 2>&1

echo "==> Starting application..."
exec dumb-init node src/index.js
