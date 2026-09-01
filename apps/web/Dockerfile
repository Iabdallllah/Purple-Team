FROM node:20-alpine AS base
WORKDIR /app

# shared package
COPY packages/shared/package.json ./packages/shared/package.json
COPY packages/shared/src ./packages/shared/src
COPY packages/shared/tsconfig.json ./packages/shared/tsconfig.json
RUN cd packages/shared && npm ci 2>&1 | tail -5 || npm install 2>&1 | tail -5; npm run build 2>&1 | tail -5 || true

# web deps
COPY apps/web/package.json ./apps/web/package.json
COPY apps/web/package-lock.json* ./apps/web/
RUN cd apps/web && npm ci 2>&1 | tail -5 || npm install 2>&1 | tail -5

# web source (next.config, tailwind, src, etc)
COPY apps/web ./apps/web
WORKDIR /app/apps/web
RUN npm run build 2>&1 | tail -20

EXPOSE 3000
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=http://api:8001

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -q --spider http://localhost:3000/ || exit 1

CMD ["npm", "start"]
