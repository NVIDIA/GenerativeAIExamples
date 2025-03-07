FROM node:18-alpine as build
WORKDIR /app

# Install build dependencies first
RUN apk add --no-cache python3 make g++ build-base

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy rest of the files
COPY env.txt .env
#COPY .certs /app/.certs
COPY . ./

# Force clean install of dependencies to avoid version conflicts
RUN rm -rf node_modules
RUN npm install --force
RUN npm run build

EXPOSE 3002
CMD ["npm", "start"]
