.PHONY: build run test clean dev

# Build the Go backend
build:
	cd go-backend && go build -o bin/cmdb-server ./cmd/server

# Run the server locally
run: build
	cd go-backend && ./bin/cmdb-server --role=all

# Development mode with hot reload (requires air)
dev:
	cd go-backend && air -c .air.toml

# Run tests
test:
	cd go-backend && go test ./...

# Run tests with coverage
test-cover:
	cd go-backend && go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Clean build artifacts
clean:
	rm -rf go-backend/bin go-backend/coverage.out go-backend/coverage.html

# Tidy modules
tidy:
	cd go-backend && go mod tidy

# Format code
fmt:
	cd go-backend && go fmt ./...

# Lint (requires golangci-lint)
lint:
	cd go-backend && golangci-lint run

# Generate OpenAPI contract check script
contract-check:
	chmod +x scripts/contract_check.sh

# Run contract validation
validate: build
	./scripts/contract_check.sh

# Docker build
docker-build:
	docker build -t cmdb-go-backend ./go-backend

# Docker run
docker-run: docker-build
	docker run -p 8080:8080 \
		-e DB_DSN="postgres://cmdb:cmdb_dev@host.docker.internal:5432/cmdb_go?sslmode=disable" \
		-e REDIS_ADDR="host.docker.internal:6379" \
		-e REDIS_DB=1 \
		-e CMDB_ROLE=all \
		cmdb-go-backend

# Database migration
migrate-up:
	golang-migrate -path go-backend/migrations -database "postgres://cmdb:cmdb_dev@localhost:5432/cmdb_go?sslmode=disable" up

migrate-down:
	golang-migrate -path go-backend/migrations -database "postgres://cmdb:cmdb_dev@localhost:5432/cmdb_go?sslmode=disable" down

# Performance comparison
perf-compare:
	./scripts/perf_compare.sh
