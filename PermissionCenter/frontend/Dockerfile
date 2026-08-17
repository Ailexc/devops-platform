# 前端管理台运行时镜像：nginx + 宿主机预构建 dist
# 背景：容器内 npm install 网络不稳定（lockfile 锁定 registry 容器内不可达），
# 而宿主机 npm 可用 → 由 Makefile 先 `npm ci && npm run build` 到 dist/，此处仅拷贝 + 反代。
# 构建：make frontend-image（内部先宿主机构建 dist 再 docker build）
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html
EXPOSE 80
