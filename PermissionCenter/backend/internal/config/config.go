// Package config 加载服务配置（环境变量，默认值对齐 deploy/.env.example）
package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	HTTPAddr string
	LogLevel string

	PGDSN     string
	RedisAddr string

	JWTSecret     string
	JWTAccessTTL  time.Duration
	JWTRefreshTTL time.Duration

	OpenFGAServerURL string

	CMDBBaseURL      string
	CMDBWebhookToken string
	IdentityBaseURL  string

	// PEP→PDP 共享密钥（防绕过网关直连 PDP）
	PEPSharedSecret string

	// 缓存 TTL
	DecisionCacheTTL time.Duration
	PolicyCacheTTL   time.Duration
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func getdur(key string, def time.Duration) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
	}
	return def
}

func getbool(key string, def bool) bool {
	if v := os.Getenv(key); v != "" {
		if b, err := strconv.ParseBool(v); err == nil {
			return b
		}
	}
	return def
}

func Load() *Config {
	return &Config{
		HTTPAddr:          getenv("IAM_HTTP_ADDR", ":8080"),
		LogLevel:          getenv("IAM_LOG_LEVEL", "info"),
		PGDSN:             getenv("PG_DSN", "postgres://iam:iam@localhost:5432/iam?sslmode=disable"),
		RedisAddr:         getenv("REDIS_ADDR", "localhost:6379"),
		JWTSecret:         getenv("JWT_SECRET", "change-me-in-prod"),
		JWTAccessTTL:      getdur("JWT_ACCESS_TTL", 15*time.Minute),
		JWTRefreshTTL:     getdur("JWT_REFRESH_TTL", 7*24*time.Hour),
		OpenFGAServerURL:  getenv("OPENFGA_ADDR", "localhost:8081"),
		CMDBBaseURL:       getenv("CMDB_BASE_URL", "http://localhost:8090"),
		CMDBWebhookToken:  getenv("CMDB_WEBHOOK_TOKEN", "cmdb-webhook-secret"),
		IdentityBaseURL:   getenv("IDENTITY_BASE_URL", "http://localhost:8091"),
		PEPSharedSecret:   getenv("PEP_SHARED_SECRET", "pep-shared-secret"),
		DecisionCacheTTL:  60 * time.Second,
		PolicyCacheTTL:    30 * time.Second,
	}
}