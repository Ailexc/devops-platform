FROM python:3.11-slim
# 依赖源可覆盖：默认官方公网源；内网部署经 compose build args 注入缓存端点（deploy/server/.env.server）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_FLAGS=


WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i ${PIP_INDEX_URL} ${PIP_FLAGS}

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令（会在 entrypoint 中被覆盖）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
