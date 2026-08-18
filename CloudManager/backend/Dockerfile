FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（中国 ECS：使用阿里云镜像）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 复制项目代码
COPY . .

EXPOSE 8000

# 启动脚本：等待 MySQL → 迁移 → 种子数据 → 启动服务
# 注意：不映射端口到宿主机，通过 OrbStack 域名访问
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
