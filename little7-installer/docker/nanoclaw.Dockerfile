# Base image with Node runtime
FROM node:20-slim

# Set working directory inside container
WORKDIR /app

# Install minimal system dependencies
RUN apt update \
    && apt install -y git \
    && rm -rf /var/lib/apt/lists/*

# Copy package definition first (better Docker layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install --unsafe-perm

# Copy application source
COPY . .

# Build step (if project provides build script)
RUN npm run build || true

# Default runtime command
CMD ["npm", "start"]
