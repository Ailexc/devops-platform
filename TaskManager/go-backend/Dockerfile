FROM golang:1.24-alpine AS builder

# 中国 ECS：proxy.golang.org 不可达，使用 goproxy.cn
ENV GOPROXY=https://goproxy.cn,direct

WORKDIR /app

# Allow Go to auto-download the required toolchain (go.mod requires 1.24)
ENV GOTOOLCHAIN=auto

# 中国 ECS：apk 默认源 dl-cdn.alpinelinux.org 慢 → 改用阿里云 alpine 镜像
RUN sed -i 's|dl-cdn.alpinelinux.org|mirrors.aliyun.com|g' /etc/apk/repositories

# Install git and ca-certs for HTTPS
RUN apk add --no-cache git ca-certificates

# Copy go.mod and go.sum for dependency caching
COPY go.mod go.sum* ./
RUN go mod download

# Copy source code
COPY . .

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/cmdb-server ./cmd/server

# Runtime
FROM alpine:3.19

# 中国 ECS：apk 默认源 dl-cdn.alpinelinux.org 慢 → 改用阿里云 alpine 镜像
RUN sed -i 's|dl-cdn.alpinelinux.org|mirrors.aliyun.com|g' /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/cmdb-server .

EXPOSE 8080

ENTRYPOINT ["./cmdb-server"]
CMD ["--role=all"]
