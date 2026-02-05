FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with Nginx (Optional, since FastAPI serves it)
# For now, we just want the build output to be accessible
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/dist ./dist
