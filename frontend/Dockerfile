# Multi-stage build for optimized production image
# FROM docker.m.daocloud.io/library/node:18-alpine as builder
FROM node:18-alpine as builder


WORKDIR /app

# Inject Vite env variables at build time so the generated bundle
# talks to the correct backend/API services.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_AGORA_APP_ID=
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_AGORA_APP_ID=${VITE_AGORA_APP_ID}

# Copy package files
COPY package*.json ./

# Install dependencies (needs dev deps for build tooling like tsc/vite)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM docker.m.daocloud.io/library/nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
