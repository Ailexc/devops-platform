FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

FROM alpine:3.20
# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]