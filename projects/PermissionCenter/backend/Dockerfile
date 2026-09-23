# 运行时镜像：alpine 最小化 + 宿主机预编译二进制
# 背景：本机 Docker 镜像源（daocloud）对 docker.io/library/golang 拉取缓慢/不可用，
# 而宿主机 Go 工具链可用 → 由 Makefile 先 `go build` 到 bin/，此处仅拷贝 + 运行。
# 构建：make backend-image（内部先编译 5 个二进制再 docker build；S1 后含 iam-sync）
FROM alpine:3.20
# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata

# 二进制：iam-server / iam-sync / mock-cmdb / mock-identity / iam-agent（对应 cmd/*）
COPY bin/ /usr/local/bin/

WORKDIR /app
EXPOSE 8080 8090 8091 9090
# 通过 compose command 选择要运行的二进制（如 command: iam-server）
ENTRYPOINT []
