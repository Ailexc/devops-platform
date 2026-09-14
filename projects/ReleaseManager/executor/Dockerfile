FROM python:3.11-slim

# pip 使用国内镜像加速
RUN pip config set global.index-url http://pypi.home.ailexc.com/simple/
RUN pip config set global.trusted-host pypi.home.ailexc.com

# 安装 Docker CLI 和 kubectl（用于 CI 构建 + CD 部署）
# debian 官方源保留（内网 deb.debian.org 劫持自动走 AnyHaven apt 缓存）；
# docker-ce / k8s 无缓存面，仍用阿里云镜像源
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list \
    && curl -fsSL https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg \
    && chmod a+r /etc/apt/keyrings/kubernetes-apt-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli kubectl \
    && mv /usr/bin/kubectl /usr/local/bin/kubectl.real \
    && printf '#!/bin/sh\nexec /usr/local/bin/kubectl.real --insecure-skip-tls-verify "$@"\n' > /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i http://pypi.home.ailexc.com/simple --trusted-host pypi.home.ailexc.com

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8765

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
