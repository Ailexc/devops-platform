# 统一门户前端 - 生产容器
# 构建：宿主机构建 dist → nginx 运行时（容器内 npm install 网络不稳定）

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
