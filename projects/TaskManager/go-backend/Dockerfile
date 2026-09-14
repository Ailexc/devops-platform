FROM golang:1.24-alpine AS builder

# 依赖源可覆盖：默认官方源；内网部署注入 http://goproxy.home.ailexc.com
ARG GOPROXY=https://proxy.golang.org,direct
ENV GOPROXY=${GOPROXY}

WORKDIR /app

# Allow Go to auto-download the required toolchain (go.mod requires 1.24)
ENV GOTOOLCHAIN=auto

# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories

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

# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/cmdb-server .

EXPOSE 8080

ENTRYPOINT ["./cmdb-server"]
CMD ["--role=all"]
