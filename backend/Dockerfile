FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY prisma ./prisma
COPY src ./src
RUN npx prisma generate

FROM node:22-alpine AS production
WORKDIR /app

RUN apk add --no-cache dumb-init
RUN npm install -g prisma@^6.2.1

RUN addgroup -S devshort && adduser -S devshort -G devshort

COPY --from=deps --chown=devshort:devshort /app/node_modules ./node_modules
COPY --from=builder --chown=devshort:devshort /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder --chown=devshort:devshort /app/node_modules/@prisma ./node_modules/@prisma

COPY --from=builder --chown=devshort:devshort /app/prisma ./prisma
COPY --from=builder --chown=devshort:devshort /app/src ./src
COPY --from=builder --chown=devshort:devshort /app/package.json ./

COPY docker-entrypoint.sh /usr/local/bin/
COPY wait-for-db.cjs /app/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER devshort
EXPOSE 4000
ENTRYPOINT ["docker-entrypoint.sh"]
