# Build stage
FROM golang:1.26-alpine AS builder
# 依赖源可覆盖：默认官方源；内网部署注入 http://goproxy.home.ailexc.com
ARG GOPROXY=https://proxy.golang.org,direct
ENV GOPROXY=${GOPROXY}
# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories
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
# 依赖源可覆盖：默认官方源；内网部署注入 http://alpine.home.ailexc.com
ARG APK_MIRROR=https://dl-cdn.alpinelinux.org
RUN sed -i "s|https://dl-cdn.alpinelinux.org|${APK_MIRROR}|g" /etc/apk/repositories
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /bin/api /bin/worker /bin/seed /usr/local/bin/
COPY docs/ /app/docs/
COPY migrations/ /app/migrations/
EXPOSE 8000
