# Build stage
FROM golang:1.26-alpine AS builder
# 中国 ECS：proxy.golang.org 不可达，使用 goproxy.cn
ENV GOPROXY=https://goproxy.cn,direct
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
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /bin/api /bin/worker /bin/seed /usr/local/bin/
COPY docs/ /app/docs/
COPY migrations/ /app/migrations/
EXPOSE 8000
