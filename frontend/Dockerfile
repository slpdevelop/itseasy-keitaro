# syntax=docker/dockerfile:1

# ---------------------------------------------------------------
# Этап 1: зависимости (общий базовый слой)
# ---------------------------------------------------------------
FROM node:20-alpine AS deps

ENV VITE_API_BASE_URL=/api/v1
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------
# Этап 2: production — статичная сборка Vite + отдача через nginx
# ---------------------------------------------------------------
FROM deps AS builder
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# ---------------------------------------------------------------
# Этап 3: development — Vite dev server с hot reload
# ---------------------------------------------------------------
FROM deps AS development
WORKDIR /app
COPY . .
# Относительный путь — Vite проксирует /api на backend через server.proxy.
ENV VITE_API_BASE_URL=/api/v1
ENV CHOKIDAR_USEPOLLING=true
EXPOSE 80
CMD ["npm", "run", "dev", "--", "--host", "--port", "80"]
