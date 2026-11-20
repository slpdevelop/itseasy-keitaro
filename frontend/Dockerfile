# Frontend image for Keitaro Campaign Manager.
# Build: docker compose -f backend/docker-compose.yml build frontend
# Run:   docker compose -f backend/docker-compose.yml up frontend

# ---------------------------------------------------------------
# Stage 1: build the Vite + React application
# ---------------------------------------------------------------
FROM node:20-alpine AS builder

ENV VITE_API_BASE_URL=/api/v1

WORKDIR /app

# Install dependencies first (layer caching on dependency changes only).
COPY package.json package-lock.json ./
RUN npm ci

# Copy sources and build.
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ---------------------------------------------------------------
# Stage 2: serve static files with nginx and proxy /api to backend
# ---------------------------------------------------------------
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
