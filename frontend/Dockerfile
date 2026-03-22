FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run Vite dev server with --host to expose it outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
