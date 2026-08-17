FROM python:3.11-slim

# pip 使用国内镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip config set global.trusted-host mirrors.aliyun.com

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令（会在 entrypoint 中被覆盖）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
