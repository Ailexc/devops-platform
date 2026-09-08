package config

import (
	"log"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	// Database
	DatabaseURL string

	// Redis
	RedisURL string

	// Server
	APIPort string

	// Worker
	WorkerConcurrency int
	WorkerQueues      []string

	// App
	OutputDir string
	DocsDir   string
	Debug     bool

	// Seed（启动幂等种子）
	SeedTotal int  // 空库首灌的演示事件条数，默认 1000
	SeedForce bool // 是否强制清空重灌（默认 false，仅清库场景使用）
}

var AppConfig *Config

func Load() *Config {
	_ = godotenv.Load()

	cfg := &Config{
		DatabaseURL:        getEnv("DATABASE_URL", "postgres://eventuser:eventpass@localhost:5432/eventdb?sslmode=disable"),
		RedisURL:           getEnv("REDIS_URL", "redis://localhost:6379/0"),
		APIPort:            getEnv("API_PORT", "8000"),
		WorkerConcurrency:  getEnvInt("WORKER_CONCURRENCY", 10),
		WorkerQueues:       []string{"events", "events.high", "tasklab"},
		OutputDir:          getEnv("OUTPUT_DIR", "../output"),
		DocsDir:            getEnv("DOCS_DIR", "../docs"),
		Debug:              getEnvBool("DEBUG", false),
		SeedTotal:          getEnvInt("SEED_TOTAL", 1000),
		SeedForce:          getEnvBool("SEED_FORCE", false),
	}

	AppConfig = cfg
	return cfg
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	log.Printf("Warning: invalid int for %s, using default %d", key, fallback)
	return fallback
}

func getEnvBool(key string, fallback bool) bool {
	if v := os.Getenv(key); v != "" {
		if b, err := strconv.ParseBool(v); err == nil {
			return b
		}
	}
	return fallback
}
