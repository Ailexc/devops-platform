FROM python:3.11-slim

WORKDIR /app

# 配置 pip 国内镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip config set global.trusted-host mirrors.aliyun.com

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
