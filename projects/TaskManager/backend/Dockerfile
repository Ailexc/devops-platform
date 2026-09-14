FROM python:3.11-slim
# 依赖源可覆盖：默认官方公网源；内网部署经 compose build args 注入缓存端点（deploy/server/.env.server）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_FLAGS=

WORKDIR /app


COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i ${PIP_INDEX_URL} ${PIP_FLAGS}

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
