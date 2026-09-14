FROM python:3.11-slim

# pip 使用国内镜像加速
RUN pip config set global.index-url http://pypi.home.ailexc.com/simple/
RUN pip config set global.trusted-host pypi.home.ailexc.com

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
# BuildKit 缓存挂载：pip 缓存存 builder 不进镜像层（rebuild 命中缓存秒过，镜像体积不变）
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i http://pypi.home.ailexc.com/simple --trusted-host pypi.home.ailexc.com

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令（会在 entrypoint 中被覆盖）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
