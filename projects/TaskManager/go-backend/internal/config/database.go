package config

import (
	"fmt"
	"log/slog"

	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// NewDB creates a new GORM database connection.
func NewDB(dsn string) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get underlying sql.DB: %w", err)
	}

	// Connection pool settings
	sqlDB.SetMaxOpenConns(25)
	sqlDB.SetMaxIdleConns(5)

	slog.Info("database connected", "dsn", maskDSN(dsn))
	return db, nil
}

// NewRedisClient creates a new Redis client.
func NewRedisClient(addr string, db int, pass string) (*redis.Client, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		DB:       db,
		Password: pass,
	})

	// We don't have a context here easily, just return the client
	slog.Info("redis client created", "addr", addr, "db", db)
	return client, nil
}

func maskDSN(dsn string) string {
	// Simple masking: keep host and db, hide password
	if len(dsn) > 30 {
		return dsn[:20] + "***" + dsn[len(dsn)-10:]
	}
	return dsn
}
