package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"cmdb-go/internal/api"
	"cmdb-go/internal/config"
	"cmdb-go/internal/model"
	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/alert"
	"cmdb-go/internal/pkg/checkpoint"
	"cmdb-go/internal/pkg/cmdbstore"
	"cmdb-go/internal/pkg/lock"
	"cmdb-go/internal/service"
	"cmdb-go/internal/tasktypes"
	"cmdb-go/internal/worker"

	"github.com/hibiken/asynq"
	"github.com/spf13/pflag"
	"gorm.io/gorm"
)

// getExecutableDir returns the directory of the running executable.
func getExecutableDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

func main() {
	// Command line flags
	seedFlag := pflag.Bool("seed", false, "Seed demo data on startup")
	resetFlag := pflag.Bool("reset", false, "Reset all data before seeding (use with --seed)")
	pflag.Parse()

	// Load configuration
	cfg := config.Load()

	// Setup logger
	config.SetupLogger(cfg.Log.Level)
	slog.Info("starting cmdb-go server",
		"role", cfg.Server.Role,
		"port", cfg.Server.Port,
	)

	// Connect to database
	db, err := config.NewDB(cfg.Database.DSN)
	if err != nil {
		slog.Error("database connection failed", "error", err)
		os.Exit(1)
	}

	// Auto-migrate tables
	if err := autoMigrate(db); err != nil {
		slog.Error("auto-migrate failed", "error", err)
		os.Exit(1)
	}

	// Connect to Redis
	rdb, err := config.NewRedisClient(cfg.Redis.Addr, cfg.Redis.DB, cfg.Redis.Pass)
	if err != nil {
		slog.Error("redis connection failed", "error", err)
		os.Exit(1)
	}
	defer rdb.Close()

	// Initialize shared packages
	lockMgr := lock.NewManager(rdb)
	_ = alert.NewEngine()
	_ = checkpoint.NewManager(rdb)
	store := cmdbstore.New(rdb)

	// Initialize resource registry
	registry := orchestrator.DefaultRegistry()

	// Initialize services
	configSvc := service.NewConfigService(db)
	configSvc.SeedDefaultData(context.Background())

	// Seed demo data if requested
	if *seedFlag {
		seedSvc := service.NewSeedService(db)
		if err := seedSvc.SeedDemoData(context.Background(), *resetFlag); err != nil {
			slog.Error("seed failed", "error", err)
		}
	}

	scheduleSvc := service.NewScheduleService(db)
	executionSvc := service.NewExecutionService(db, lockMgr, registry)
	treeSvc := service.NewTaskTreeService(db, registry, lockMgr, configSvc, scheduleSvc)
	metricsSvc := service.NewMetricsService(db, store, registry)

	// Create asynq client for enqueuing tasks
	asynqClient := asynq.NewClient(asynq.RedisClientOpt{
		Addr:     cfg.Redis.Addr,
		DB:       cfg.Redis.DB,
		Password: cfg.Redis.Pass,
	})
	defer asynqClient.Close()

	// Set the asynq client in execution service for async dispatch
	executionSvc.SetAsynqClient(asynqClient)

	// Start asynq worker if role includes worker
	if cfg.Server.Role == "worker" || cfg.Server.Role == "all" {
		go startAsynqWorker(cfg, db, registry, executionSvc, store)
	}

	// Start asynq scheduler if role includes scheduler
	if cfg.Server.Role == "scheduler" || cfg.Server.Role == "all" {
		go startAsynqScheduler(cfg, asynqClient)
	}

	// Create API router
	// Resolve docs directory relative to executable location
	docsDir := filepath.Join(getExecutableDir(), "docs")
	router := api.NewRouter(
		metricsSvc,
		executionSvc,
		treeSvc,
		configSvc,
		scheduleSvc,
		lockMgr,
		docsDir,
		asynqClient,
	)

	// Start server
	addr := fmt.Sprintf(":%d", cfg.Server.Port)
	slog.Info("server starting", "addr", addr)

	// Graceful shutdown
	go func() {
		if err := router.Engine().Run(addr); err != nil {
			slog.Error("server failed", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	slog.Info("shutting down server...")
}

// autoMigrate creates/updates database tables.
func autoMigrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&model.ExecutionRecord{},
		&model.DailyTaskStat{},
		&model.AccountRegion{},
		&model.PeriodicTask{},
	)
}

// startAsynqWorker starts the asynq worker process.
func startAsynqWorker(cfg *config.Config, db *gorm.DB, registry *orchestrator.Registry, executionSvc *service.ExecutionService, store *cmdbstore.Store) {
	slog.Info("starting asynq worker")

	srv := asynq.NewServer(
		asynq.RedisClientOpt{
			Addr:     cfg.Redis.Addr,
			DB:       cfg.Redis.DB,
			Password: cfg.Redis.Pass,
		},
		asynq.Config{
			Concurrency: 10,
			Queues: map[string]int{
				"critical": 6,
				"default":  3,
				"low":      1,
			},
		},
	)

	mux := asynq.NewServeMux()
	orchHandler := worker.NewOrchestratorHandler(db, registry, executionSvc, store)
	syncHandler := worker.NewResourceSyncHandler(db, store, registry)
	relationHandler := worker.NewRelationTaskHandler(db, store)
	testHandler := worker.NewTestTaskHandler(db, store)

	mux.HandleFunc(tasktypes.TaskTypeOrchestrate, orchHandler.Handle)
	mux.HandleFunc(tasktypes.TaskTypeResourceSync, syncHandler.HandleTask)
	mux.HandleFunc(tasktypes.TaskTypeRelationBuild, relationHandler.HandleTask)
	mux.HandleFunc(tasktypes.TaskTypeTestTask, testHandler.HandleTestTask)

	if err := srv.Run(mux); err != nil {
		slog.Error("asynq worker failed", "error", err)
	}
}

// startAsynqScheduler starts the asynq scheduler for periodic tasks.
func startAsynqScheduler(cfg *config.Config, client *asynq.Client) {
	slog.Info("starting asynq scheduler")

	scheduler := asynq.NewScheduler(
		asynq.RedisClientOpt{
			Addr:     cfg.Redis.Addr,
			DB:       cfg.Redis.DB,
			Password: cfg.Redis.Pass,
		},
		nil,
	)

	// TODO: Load periodic tasks from DB and register them
	// For now, the scheduler runs empty

	if err := scheduler.Run(); err != nil {
		slog.Error("asynq scheduler failed", "error", err)
	}
}
