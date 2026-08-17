package config

import (
	"log/slog"
	"os"
	"strconv"
	"strings"

	"github.com/spf13/viper"
)

// Config holds all application configuration.
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	AWS      AWSConfig
	Log      LogConfig
}

type ServerConfig struct {
	Port int
	Mode string // debug, release, test
	Role string // api, worker, scheduler, all
}

type DatabaseConfig struct {
	DSN string
}

type RedisConfig struct {
	Addr string
	DB   int
	Pass string
}

type AWSConfig struct {
	Region string
}

type LogConfig struct {
	Level string // debug, info, warn, error
}

// Load reads configuration from environment variables and config file.
func Load() *Config {
	v := viper.New()

	// Defaults
	v.SetDefault("server.port", 8080)
	v.SetDefault("server.mode", "debug")
	v.SetDefault("server.role", "all")
	v.SetDefault("database.dsn", "postgres://cmdb:cmdb_dev@localhost:5432/cmdb_go?sslmode=disable")
	v.SetDefault("redis.addr", "localhost:6379")
	v.SetDefault("redis.db", 1)
	v.SetDefault("redis.pass", "")
	v.SetDefault("aws.region", "ap-northeast-1")
	v.SetDefault("log.level", "info")

	// Environment variable overrides
	v.SetEnvPrefix("CMDB")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// Explicit env mappings
	if dsn := os.Getenv("DB_DSN"); dsn != "" {
		v.Set("database.dsn", dsn)
	}
	if addr := os.Getenv("REDIS_ADDR"); addr != "" {
		v.Set("redis.addr", addr)
	}
	if db := os.Getenv("REDIS_DB"); db != "" {
		if n, err := strconv.Atoi(db); err == nil {
			v.Set("redis.db", n)
		}
	}
	if pass := os.Getenv("REDIS_PASS"); pass != "" {
		v.Set("redis.pass", pass)
	}
	if region := os.Getenv("AWS_REGION"); region != "" {
		v.Set("aws.region", region)
	}
	if role := os.Getenv("CMDB_ROLE"); role != "" {
		v.Set("server.role", role)
	}
	if port := os.Getenv("PORT"); port != "" {
		if n, err := strconv.Atoi(port); err == nil {
			v.Set("server.port", n)
		}
	}

	// Config file (optional)
	v.SetConfigName("config")
	v.SetConfigType("yaml")
	v.AddConfigPath(".")
	v.AddConfigPath("./configs")
	_ = v.ReadInConfig() // ignore if not found

	cfg := &Config{}
	if err := v.Unmarshal(cfg); err != nil {
		slog.Error("failed to unmarshal config", "error", err)
		os.Exit(1)
	}

	return cfg
}

// SetupLogger configures structured logging based on config.
func SetupLogger(level string) {
	var lvl slog.Level
	switch strings.ToLower(level) {
	case "debug":
		lvl = slog.LevelDebug
	case "warn":
		lvl = slog.LevelWarn
	case "error":
		lvl = slog.LevelError
	default:
		lvl = slog.LevelInfo
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: lvl,
	}))
	slog.SetDefault(logger)
}
