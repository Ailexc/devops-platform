FROM node:20-alpine
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION
WORKDIR /app
COPY package.json ./
RUN npm install --production --registry=https://registry.npmmirror.com
COPY server.js .
EXPOSE 8080
CMD ["node", "server.js"]