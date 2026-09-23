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

	// 数据契约巡检与新鲜度（清单 A4/A6，2.3.1 确认制状态机）
	PatrolInterval           time.Duration // 巡检周期：指纹比对+增量同步+确认制时钟刷新（默认 5m；demo 10s 分钟级演示三态）
	ReconcileInterval        time.Duration // 深对账周期：全量三类差异兜底（默认 24h；demo 可手动 POST /sync/reconcile）
	StrongConsistencyTimeout time.Duration // 强一致档指纹快查+前置同步的热路径超时（超时按本地投影判定，不阻塞）
	// 同步组件独立进程 iam-sync 专属（清单 S7 env 清单）
	SyncHealthAddr     string        // healthz 仅容器内网（默认 :8090；宿主 8090 已被 devops-gateway 占用——compose 禁发布宿主口）
	ReconcileLockTTL   time.Duration // 深对账单活锁 TTL（单轮分钟级，独立于周期/2，默认 10m）
	WorkerClaimMinIdle time.Duration // 消费组 XAUTOCLAIM min-idle（S3，默认 60s）
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
		OpenFGAServerURL:         getenv("OPENFGA_ADDR", "localhost:8081"),
		CMDBBaseURL:              getenv("CMDB_BASE_URL", "http://localhost:8090"),
		CMDBWebhookToken:         getenv("CMDB_WEBHOOK_TOKEN", "cmdb-webhook-secret"),
		IdentityBaseURL:          getenv("IDENTITY_BASE_URL", "http://localhost:8091"),
		PEPSharedSecret:          getenv("PEP_SHARED_SECRET", "pep-shared-secret"),
		DecisionCacheTTL:         60 * time.Second,
		PolicyCacheTTL:           30 * time.Second,
		PatrolInterval:           getdur("PATROL_INTERVAL", 5*time.Minute),
		ReconcileInterval:        getdur("RECONCILE_INTERVAL", 24*time.Hour),
		StrongConsistencyTimeout: getdur("STRONG_CONSISTENCY_TIMEOUT", 2*time.Second),
		SyncHealthAddr:           getenv("SYNC_HEALTH_ADDR", ":8090"),
		ReconcileLockTTL:         getdur("RECONCILE_LOCK_TTL", 10*time.Minute),
		WorkerClaimMinIdle:       getdur("WORKER_CLAIM_MIN_IDLE", 60*time.Second),
	}
}
