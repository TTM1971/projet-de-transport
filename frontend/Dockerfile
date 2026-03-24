# Étape build — image utilisée par docker-compose.prod.yml (export vers volume Nginx)
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

# Développement — cible par défaut (docker compose dev)
FROM node:18-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true
ENV DANGEROUSLY_DISABLE_HOST_CHECK=true
CMD ["npm", "start"]
