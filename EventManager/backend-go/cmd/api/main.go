package main

import (
	"log"
	"strings"

	"github.com/hibiken/asynq"
	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	api "event-flow/internal/api"
	"event-flow/internal/config"
	"event-flow/internal/eventhandler"
	"event-flow/internal/model"
	"event-flow/internal/repository"
	"event-flow/internal/tasklab"
	"event-flow/internal/worker"
)

func main() {
	// ── Load config ─────────────────────────────────────────────
	cfg := config.Load()
	log.Printf("Starting API server on port %s", cfg.APIPort)

	// ── Init event handler registry ─────────────────────────────
	eventhandler.Init()

	// ── Connect to PostgreSQL ───────────────────────────────────
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// ── AutoMigrate models ─────────────────────────────────────
	if err := db.AutoMigrate(
		&model.Event{},
		&model.EventLog{},
		&model.EventHandlerConfig{},
	); err != nil {
		log.Fatalf("Failed to auto-migrate: %v", err)
	}
	log.Println("Database migration complete")

	// ── Connect to Redis for asynq ──────────────────────────────
	redisAddr := strings.TrimPrefix(cfg.RedisURL, "redis://")
	redisAddr = strings.SplitN(redisAddr, "/", 2)[0] // strip DB selector

	inspector := asynq.NewInspector(asynq.RedisClientOpt{Addr: redisAddr})
	client := asynq.NewClient(asynq.RedisClientOpt{Addr: redisAddr})

	rdb := redis.NewClient(&redis.Options{Addr: redisAddr})
	statusStore := tasklab.NewStatusStore(rdb)

	// ── Create repositories ─────────────────────────────────────
	eventRepo := repository.NewEventRepo(db)
	logRepo := repository.NewEventLogRepo(db)

	// ── Create dispatcher ───────────────────────────────────────
	dispatcher := worker.NewAsynqDispatcher(redisAddr)
	defer dispatcher.Close()

	// ── Setup router ────────────────────────────────────────────
	router := api.SetupRouter(
		db,
		eventRepo,
		logRepo,
		dispatcher,
		inspector,
		client,
		cfg.DocsDir,
		cfg.OutputDir,
		statusStore,
	)

	// ── Start server ────────────────────────────────────────────
	log.Printf("API server listening on :%s", cfg.APIPort)
	if err := router.Run(":" + cfg.APIPort); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
