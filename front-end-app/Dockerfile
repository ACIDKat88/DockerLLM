# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files for better caching
COPY package*.json ./

# Install dependencies with clean npm cache
RUN npm ci && \
    npm cache clean --force

# Copy the rest of the application files
COPY . .

# Build the frontend app
RUN npm run build

# Production stage
FROM node:18-alpine

# Install serve globally - no need for vite in production
RUN npm install -g serve

# Create a non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy the built files from builder stage
COPY --from=builder /app/dist ./dist

# Copy the public directory for static assets
COPY --from=builder /app/public ./public

# Create images directory in dist and copy logo
USER root
RUN mkdir -p ./dist/images && \
    cp -r ./public/images/* ./dist/images/ && \
    ls -la ./dist/images

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port 5173
EXPOSE 5173

# Add health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:5173 || exit 1

# Start the frontend using serve for production
CMD ["serve", "-s", "dist", "-l", "5173"]
