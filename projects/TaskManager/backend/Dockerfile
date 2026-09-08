FROM python:3.11-slim

WORKDIR /app

# 配置 pip 国内镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip config set global.trusted-host mirrors.aliyun.com

COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
