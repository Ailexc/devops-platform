FROM python:3.11-slim
# 依赖源可覆盖：默认官方公网源；内网部署经 compose build args 注入缓存端点（deploy/server/.env.server）
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_FLAGS=
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX_URL} ${PIP_FLAGS}
COPY main.py .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]