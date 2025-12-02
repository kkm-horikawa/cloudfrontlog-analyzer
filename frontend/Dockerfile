# Frontend Dockerfile for CloudFront Analyzer
FROM node:22-slim

# Set working directory
WORKDIR /app
RUN chown node:node /app

# Switch to node user BEFORE installing dependencies
USER node

# Copy package files and install as non-root
COPY --chown=node:node package*.json ./
RUN npm ci

# Copy application code
COPY --chown=node:node . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
