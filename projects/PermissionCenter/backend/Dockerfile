# 运行时镜像：alpine 最小化 + 宿主机预编译二进制
# 背景：本机 Docker 镜像源（daocloud）对 docker.io/library/golang 拉取缓慢/不可用，
# 而宿主机 Go 工具链可用 → 由 Makefile 先 `go build` 到 bin/，此处仅拷贝 + 运行。
# 构建：make backend-image（内部先编译 4 个二进制再 docker build）
FROM alpine:3.20
# 中国 ECS：apk 默认源 dl-cdn.alpinelinux.org 慢 → 改用阿里云 alpine 镜像
RUN sed -i 's|dl-cdn.alpinelinux.org|mirrors.aliyun.com|g' /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata

# 二进制：iam-server / mock-cmdb / mock-identity / iam-agent（对应 cmd/*）
COPY bin/ /usr/local/bin/

WORKDIR /app
EXPOSE 8080 8090 8091 9090
# 通过 compose command 选择要运行的二进制（如 command: iam-server）
ENTRYPOINT []
