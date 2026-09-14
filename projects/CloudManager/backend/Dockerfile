FROM python:3.11-slim
# 依赖源可覆盖：默认官方公网源；内网部署经 compose build args 注入缓存端点（deploy/server/.env.server）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_FLAGS=

WORKDIR /app


# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（中国 ECS：使用阿里云镜像）
COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i ${PIP_INDEX_URL} ${PIP_FLAGS}

# 复制项目代码
COPY . .

EXPOSE 8000

# 启动脚本：等待 MySQL → 迁移 → 种子数据 → 启动服务
# 注意：不映射端口到宿主机，通过 OrbStack 域名访问
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
