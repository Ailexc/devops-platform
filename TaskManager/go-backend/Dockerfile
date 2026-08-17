FROM golang:1.23-alpine AS builder

WORKDIR /app

# Allow Go to auto-download the required toolchain (go.mod requires 1.24)
ENV GOTOOLCHAIN=auto

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

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/cmdb-server .

EXPOSE 8080

ENTRYPOINT ["./cmdb-server"]
CMD ["--role=all"]
