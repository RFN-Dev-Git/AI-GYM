# Base image for node
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run the Vite dev server, binding to 0.0.0.0 so it is accessible outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
