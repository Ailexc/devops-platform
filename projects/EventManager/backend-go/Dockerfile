# Build stage
FROM golang:1.26-alpine AS builder
# GOPROXY 走 AnyHaven 缓存（ARG 可覆盖；上云构建可设 goproxy.cn）
ARG GOPROXY=http://goproxy.home.ailexc.com
ENV GOPROXY=${GOPROXY}
# apk 源走 AnyHaven 缓存 http://alpine.home.ailexc.com（内网口径 http；上云构建改回 https://dl-cdn.alpinelinux.org）
RUN sed -i 's|https://dl-cdn.alpinelinux.org|http://alpine.home.ailexc.com|g' /etc/apk/repositories
RUN apk add --no-cache git
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bin/api ./cmd/api
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bin/worker ./cmd/worker
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bin/seed ./cmd/seed

# Runtime stage
FROM alpine:3.20
# apk 源走 AnyHaven 缓存 http://alpine.home.ailexc.com（内网口径 http；上云构建改回 https://dl-cdn.alpinelinux.org）
RUN sed -i 's|https://dl-cdn.alpinelinux.org|http://alpine.home.ailexc.com|g' /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /bin/api /bin/worker /bin/seed /usr/local/bin/
COPY docs/ /app/docs/
COPY migrations/ /app/migrations/
EXPOSE 8000
