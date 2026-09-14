FROM python:3.12-slim
# 依赖源可覆盖：默认官方公网源；内网部署经 compose build args 注入缓存端点（deploy/server/.env.server）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_FLAGS=

WORKDIR /srv/direct

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL} ${PIP_FLAGS}

COPY app.py jwks_auth.py ./

EXPOSE 8003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
