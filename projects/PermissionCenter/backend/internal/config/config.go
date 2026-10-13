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

	CMDBBaseURL      string
	CMDBWebhookToken string
	IdentityBaseURL  string

	// PEP→PDP 共享密钥（防绕过网关直连 PDP）
	PEPSharedSecret string

	// 缓存 TTL
	DecisionCacheTTL time.Duration
	PolicyCacheTTL   time.Duration

	// （1.5 T3）巡检/深对账/强一致档已随投影退役——对应配置一并移除
	// iam-sync 专属（清单 S7 env 清单）
	SyncHealthAddr string // healthz 仅容器内网（默认 :8090；宿主 8090 已被 devops-gateway 占用——compose 禁发布宿主口）
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
		HTTPAddr:                 getenv("IAM_HTTP_ADDR", ":8080"),
		LogLevel:                 getenv("IAM_LOG_LEVEL", "info"),
		PGDSN:                    getenv("PG_DSN", "postgres://iam:iam@localhost:5432/iam?sslmode=disable"),
		RedisAddr:                getenv("REDIS_ADDR", "localhost:6379"),
		JWTSecret:                getenv("JWT_SECRET", "change-me-in-prod"),
		JWTAccessTTL:             getdur("JWT_ACCESS_TTL", 15*time.Minute),
		JWTRefreshTTL:            getdur("JWT_REFRESH_TTL", 7*24*time.Hour),
		CMDBBaseURL:              getenv("CMDB_BASE_URL", "http://localhost:8090"),
		CMDBWebhookToken:         getenv("CMDB_WEBHOOK_TOKEN", "cmdb-webhook-secret"),
		IdentityBaseURL:          getenv("IDENTITY_BASE_URL", "http://localhost:8091"),
		PEPSharedSecret:          getenv("PEP_SHARED_SECRET", "pep-shared-secret"),
		DecisionCacheTTL:         60 * time.Second,
		PolicyCacheTTL:           30 * time.Second,
		SyncHealthAddr:           getenv("SYNC_HEALTH_ADDR", ":8090"),
	}
}
