FROM python:3.11-slim

# pip 使用国内镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip config set global.trusted-host mirrors.aliyun.com

# 安装 Docker CLI 和 kubectl（用于 CI 构建 + CD 部署）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/$(dpkg --print-architecture)/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl.real \
    && printf '#!/bin/sh\nexec /usr/local/bin/kubectl.real --insecure-skip-tls-verify "$@"\n' > /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8765

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
