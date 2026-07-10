-- CreateTable: users
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- AlterTable: urls - add new columns
ALTER TABLE "urls" ADD COLUMN "custom_alias" TEXT;
ALTER TABLE "urls" ADD COLUMN "title" TEXT;
ALTER TABLE "urls" ADD COLUMN "expires_at" TIMESTAMP(3);
ALTER TABLE "urls" ADD COLUMN "user_id" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "urls_custom_alias_key" ON "urls"("custom_alias");

-- CreateIndex
CREATE INDEX "urls_user_id_idx" ON "urls"("user_id");

-- CreateIndex (already exists for short_code, but ensure it)
CREATE INDEX "urls_short_code_idx" ON "urls"("short_code");

-- CreateIndex
CREATE INDEX "urls_custom_alias_idx" ON "urls"("custom_alias");

-- AddForeignKey
ALTER TABLE "urls" ADD CONSTRAINT "urls_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- CreateTable: click_events
CREATE TABLE "click_events" (
    "id" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "browser" TEXT,
    "browser_version" TEXT,
    "os" TEXT,
    "device_type" TEXT,
    "country" TEXT,
    "referrer" TEXT,
    "ip_hash" TEXT,
    "url_id" TEXT NOT NULL,

    CONSTRAINT "click_events_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "click_events_url_id_idx" ON "click_events"("url_id");

-- CreateIndex
CREATE INDEX "click_events_timestamp_idx" ON "click_events"("timestamp");

-- AddForeignKey
ALTER TABLE "click_events" ADD CONSTRAINT "click_events_url_id_fkey" FOREIGN KEY ("url_id") REFERENCES "urls"("id") ON DELETE CASCADE ON UPDATE CASCADE;
