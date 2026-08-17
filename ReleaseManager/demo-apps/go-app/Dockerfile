FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

FROM alpine:3.20
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]