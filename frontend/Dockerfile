FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port 8080 for Vite dev server
EXPOSE 8080

# Command to run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]
