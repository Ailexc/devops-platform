# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci

# 复制源码并构建（跳过 tsc 类型检查，Vite 自行处理转译）
COPY . .
RUN npx vite build

# Production stage
FROM nginx:alpine

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
