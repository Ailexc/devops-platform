FROM golang:1.24-alpine AS builder

# GOPROXY 走 AnyHaven 缓存（ARG 可覆盖；上云构建可设 goproxy.cn）
ARG GOPROXY=http://goproxy.home.ailexc.com
ENV GOPROXY=${GOPROXY}

WORKDIR /app

# Allow Go to auto-download the required toolchain (go.mod requires 1.24)
ENV GOTOOLCHAIN=auto

# apk 源走 AnyHaven 缓存 http://alpine.home.ailexc.com（内网口径 http；上云构建改回 https://dl-cdn.alpinelinux.org）
RUN sed -i 's|https://dl-cdn.alpinelinux.org|http://alpine.home.ailexc.com|g' /etc/apk/repositories

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

# apk 源走 AnyHaven 缓存 http://alpine.home.ailexc.com（内网口径 http；上云构建改回 https://dl-cdn.alpinelinux.org）
RUN sed -i 's|https://dl-cdn.alpinelinux.org|http://alpine.home.ailexc.com|g' /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/cmdb-server .

EXPOSE 8080

ENTRYPOINT ["./cmdb-server"]
CMD ["--role=all"]
