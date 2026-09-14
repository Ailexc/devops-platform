FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

FROM alpine:3.20
# apk 源走 AnyHaven 缓存 http://alpine.home.ailexc.com（内网口径 http；上云构建改回 https://dl-cdn.alpinelinux.org）
RUN sed -i 's|https://dl-cdn.alpinelinux.org|http://alpine.home.ailexc.com|g' /etc/apk/repositories
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]