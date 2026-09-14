FROM python:3.12-slim

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i http://pypi.home.ailexc.com/simple --trusted-host pypi.home.ailexc.com

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
