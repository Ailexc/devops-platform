package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/hibiken/asynq"
	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"event-flow/internal/config"
	"event-flow/internal/eventhandler"
	"event-flow/internal/model"
	"event-flow/internal/tasklab"
	"event-flow/internal/worker"
)

func main() {
	// ── Load config ─────────────────────────────────────────────
	cfg := config.Load()
	log.Println("Starting worker...")

	// ── Init event handler registry ─────────────────────────────
	eventhandler.Init()

	// ── Connect to PostgreSQL ───────────────────────────────────
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// ── AutoMigrate (worker should also ensure schema) ─────────
	if err := db.AutoMigrate(
		&model.Event{},
		&model.EventLog{},
		&model.EventHandlerConfig{},
	); err != nil {
		log.Fatalf("Failed to auto-migrate: %v", err)
	}

	// ── Set DB for worker ───────────────────────────────────────
	worker.SetDB(db)

	// ── Connect to Redis ────────────────────────────────────────
	redisAddr := strings.TrimPrefix(cfg.RedisURL, "redis://")
	redisAddr = strings.SplitN(redisAddr, "/", 2)[0]

	rdb := redis.NewClient(&redis.Options{Addr: redisAddr})
	statusStore := tasklab.NewStatusStore(rdb)

	srv := asynq.NewServer(
		asynq.RedisClientOpt{Addr: redisAddr},
		asynq.Config{
			Concurrency: cfg.WorkerConcurrency,
			Queues:      queueMap(cfg.WorkerQueues),
		},
	)

	// ── Register task handlers ──────────────────────────────────
	mux := asynq.NewServeMux()
	mux.HandleFunc("process_event", handleProcessEvent)
	mux.HandleFunc("demo_task", func(ctx context.Context, task *asynq.Task) error {
		return handleDemoTask(ctx, task, db, statusStore, cfg.OutputDir)
	})

	// ── Start worker ────────────────────────────────────────────
	log.Printf("Worker starting with concurrency=%d, queues=%v", cfg.WorkerConcurrency, cfg.WorkerQueues)
	if err := srv.Run(mux); err != nil {
		log.Fatalf("Worker failed: %v", err)
	}
}

// handleProcessEvent is the asynq handler for process_event tasks.
func handleProcessEvent(ctx context.Context, task *asynq.Task) error {
	var payload worker.EventPayload
	if err := json.Unmarshal(task.Payload(), &payload); err != nil {
		return err
	}
	return worker.ProcessEvent(ctx, payload.EventID)
}

// handleDemoTask is the asynq handler for demo/test-lab tasks.
func handleDemoTask(ctx context.Context, task *asynq.Task, db *gorm.DB, store *tasklab.StatusStore, outputDir string) error {
	var payload struct {
		TaskID      string `json:"task_id"`
		BatchID     string `json:"batch_id"`
		Index       int    `json:"index"`
		AsynqTaskID string `json:"asynq_task_id"`
	}
	if err := json.Unmarshal(task.Payload(), &payload); err != nil {
		return err
	}
	statusKey := payload.AsynqTaskID
	if statusKey == "" {
		statusKey = fmt.Sprintf("%s-%d", payload.BatchID, payload.Index)
	}
	log.Printf("Demo task start: task_id=%s batch_id=%s index=%d key=%s", payload.TaskID, payload.BatchID, payload.Index, statusKey)

	// Store PROGRESS state in Redis so frontend can poll
	_ = store.SetState(ctx, statusKey, "PROGRESS",
		map[string]interface{}{
			"current": payload.Index + 1,
			"total":   1,
			"status":  fmt.Sprintf("正在执行 %s 任务...", payload.TaskID),
		}, nil)

	switch payload.TaskID {
	case "fast":
		result, err := tasklab.FetchAndProcess(ctx, db, store, outputDir, payload.BatchID, payload.Index+1, 1, payload.BatchID)
		if err != nil {
			log.Printf("Demo fast task failed: %v", err)
			_ = store.SetState(ctx, statusKey, "FAILURE", map[string]interface{}{"error": err.Error()}, nil)
			return err
		}
		log.Printf("Demo fast task completed: event_id=%s file=%s", result.EventIDs, result.FilePath)
		_ = store.SetState(ctx, statusKey, "SUCCESS", nil, map[string]interface{}{
			"success":        true,
			"output_filename": result.FilePath,
			"total_posts":    result.Stats.TotalPosts,
			"top_words":      result.Stats.TopWords,
			"event_ids":      result.EventIDs,
		})
		return nil

	case "slow":
		result, err := tasklab.GenerateReport(ctx, db, store, outputDir, payload.BatchID, payload.Index+1, 1, payload.BatchID)
		if err != nil {
			log.Printf("Demo slow task failed: %v", err)
			_ = store.SetState(ctx, statusKey, "FAILURE", map[string]interface{}{"error": err.Error()}, nil)
			return err
		}
		log.Printf("Demo slow task completed: event_id=%s file=%s", result.EventIDs, result.FilePath)
		_ = store.SetState(ctx, statusKey, "SUCCESS", nil, map[string]interface{}{
			"success":        true,
			"output_filename": result.FilePath,
			"event_ids":      result.EventIDs,
		})
		return nil

	default:
		log.Printf("Unknown demo task: %s", payload.TaskID)
		return nil
	}
}

// queueMap converts a list of queue names to asynq weight map.
func queueMap(queues []string) map[string]int {
	m := make(map[string]int, len(queues))
	for _, q := range queues {
		m[q] = 1
	}
	return m
}
