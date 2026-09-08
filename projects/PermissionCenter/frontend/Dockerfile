# 前端管理台镜像：容器内多阶段构建（ECS 云端无 Node 也能构建）
# 背景：本地 OrbStack 容器内 npm registry 不可达 → 曾用宿主机 npm 预构建 dist；
#       云端 ECS 无 Node 工具链，改为容器内多阶段构建（与 CloudManager 等一致）。
# 构建：docker build -f frontend/Dockerfile -t iam-frontend frontend

# Build stage
FROM node:20-alpine AS build
WORKDIR /app
# 中国 ECS：registry.npmjs.org 慢/不可达 → 使用 npmmirror（阿里/国内镜像）
RUN npm config set registry https://registry.npmmirror.com
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
