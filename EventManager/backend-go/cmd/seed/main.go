package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strings"
	"time"

	"github.com/google/uuid"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"event-flow/internal/config"
	"event-flow/internal/model"
)

// EventTemplate mirrors the Python seed_data.py templates.
type EventTemplate struct {
	Pattern       string
	Source        string
	Events        []EventInfo
	StatusWeights [5]int // completed, failed, dlq, processing, pending
	PayloadFn     func() map[string]interface{}
}

type EventInfo struct {
	Type      string
	Resources []string
}

var templates = []EventTemplate{
	{
		Pattern:       "aws.ec2.*",
		Source:        "aws",
		StatusWeights: [5]int{75, 10, 5, 5, 5},
		Events: []EventInfo{
			{Type: "aws.ec2.state-change", Resources: []string{"i-"}},
			{Type: "aws.ec2.instance-created", Resources: []string{"i-"}},
			{Type: "aws.ec2.instance-terminated", Resources: []string{"i-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
				"instance_id":   fmt.Sprintf("i-%s", shortHex()),
				"state":         randomChoice([]string{"running", "stopped", "stopping", "pending", "terminated"}),
				"region":        randomChoice([]string{"us-east-1", "ap-northeast-1", "eu-west-1", "us-west-2"}),
				"instance_type": randomChoice([]string{"t3.medium", "t3.large", "m5.large", "c5.xlarge"}),
			}
		},
	},
	{
		Pattern:       "aws.rds.*",
		Source:        "aws",
		StatusWeights: [5]int{80, 8, 4, 4, 4},
		Events: []EventInfo{
			{Type: "aws.rds.backup-completed", Resources: []string{"db-"}},
			{Type: "aws.rds.instance-created", Resources: []string{"db-"}},
			{Type: "aws.rds.failover", Resources: []string{"db-"}},
			{Type: "aws.rds.maintenance", Resources: []string{"db-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
					"db_instance": fmt.Sprintf("db-%s-%02d", randomChoice([]string{"prod", "staging", "dev"}), rand.Intn(99)+1),
				"category":    randomChoice([]string{"backup", "maintenance", "creation", "failover", "resize"}),
				"region":      randomChoice([]string{"us-east-1", "eu-west-1", "ap-southeast-1"}),
				"storage":     randomChoiceInt([]int{100, 200, 500, 1000}),
			}
		},
	},
	{
		Pattern:       "aws.s3.*",
		Source:        "aws",
		StatusWeights: [5]int{85, 5, 2, 4, 4},
		Events: []EventInfo{
			{Type: "aws.s3.object-created", Resources: []string{"bucket-"}},
			{Type: "aws.s3.object-deleted", Resources: []string{"bucket-"}},
			{Type: "aws.s3.object-restored", Resources: []string{"bucket-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
				"bucket":     fmt.Sprintf("app-%s-%02d", randomChoice([]string{"data", "logs", "backups", "assets"}), rand.Intn(99)+1),
				"object_key": fmt.Sprintf("%s/%s.%s", randomChoice([]string{"uploads", "docs", "images", "exports"}), shortHex()[:12], randomChoice([]string{"pdf", "jpg", "json", "csv"})), 
				"action":     randomChoice([]string{"PUT", "POST", "DELETE", "COPY"}),
				"size":       rand.Intn(10*1024*1024) + 1024,
			}
		},
	},
	{
		Pattern:       "webhook.github.*",
		Source:        "github",
		StatusWeights: [5]int{88, 5, 2, 3, 2},
		Events: []EventInfo{
			{Type: "webhook.github.push", Resources: []string{"repo-"}},
			{Type: "webhook.github.pull_request", Resources: []string{"repo-"}},
			{Type: "webhook.github.issues", Resources: []string{"repo-"}},
			{Type: "webhook.github.release", Resources: []string{"repo-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
				"github_event": randomChoice([]string{"push", "pull_request", "issues", "release", "star"}),
				"repository":   fmt.Sprintf("%s/%s", randomChoice([]string{"my-org", "team-a", "open-source"}), randomChoice([]string{"frontend", "backend", "docs", "infra"})),
				"ref":          randomChoice([]string{"main", "develop", "feature/new-api", "fix/bug-123"}),
				"commits":      rand.Intn(10) + 1,
			}
		},
	},
	{
		Pattern:       "internal.health",
		Source:        "scheduler",
		StatusWeights: [5]int{98, 1, 0, 0, 1},
		Events: []EventInfo{
			{Type: "internal.health", Resources: []string{"svc-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
				"component": randomChoice([]string{"api", "celery-worker", "postgres", "redis", "rabbitmq"}),
				"check":     randomChoice([]string{"ping", "db-connectivity", "queue-depth", "memory-usage"}),
			}
		},
	},
	{
		Pattern:       "echo.*",
		Source:        "manual",
		StatusWeights: [5]int{60, 20, 10, 5, 5},
		Events: []EventInfo{
			{Type: "echo.test", Resources: []string{"test-"}},
			{Type: "echo.error", Resources: []string{"test-"}},
		},
		PayloadFn: func() map[string]interface{} {
			simulateError := rand.Float64() < 0.2
			return map[string]interface{}{
				"message":        fmt.Sprintf("Test event #%d", rand.Intn(9999)+1),
				"simulate_error": simulateError,
			}
		},
	},
}

func main() {
	cfg := config.Load()
	total := 1000

	log.Printf("🌱 Seeding %d simulated events...", total)

	// ── Connect to PostgreSQL ───────────────────────────────────
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// ── AutoMigrate ─────────────────────────────────────────────
	if err := db.AutoMigrate(
		&model.Event{},
		&model.EventLog{},
		&model.EventHandlerConfig{},
	); err != nil {
		log.Fatalf("Failed to migrate: %v", err)
	}

	// ── Clear existing data ─────────────────────────────────────
	db.Exec("TRUNCATE api_eventlog CASCADE")
	db.Exec("TRUNCATE api_event CASCADE")
	db.Exec("TRUNCATE api_eventhandlerconfig CASCADE")
	log.Println("  🗑️  Cleared existing data")

	// ── Generate events in batches ──────────────────────────────
	batchSize := 100
	eventsBatch := make([]model.Event, 0, batchSize)
	logsBatch := make([]model.EventLog, 0, batchSize*2)

	for i := 1; i <= total; i++ {
		tmpl := templates[rand.Intn(len(templates))]
		eventInfo := tmpl.Events[rand.Intn(len(tmpl.Events))]
		resourceID := eventInfo.Resources[0] + shortHex()[:10]
		receivedAt := randomPastTime(24)
		status := pickStatus(tmpl.StatusWeights)
		payload := tmpl.PayloadFn()

		// echo.error with simulate_error → force failed
		if v, ok := payload["simulate_error"]; ok && v.(bool) {
			status = model.StatusFailed
		}

		event := model.Event{
			ID:         uuid.New(),
			EventType:  eventInfo.Type,
			Source:     tmpl.Source,
			DetailType: strings.Split(eventInfo.Type, ".")[len(strings.Split(eventInfo.Type, "."))-1],
			ResourceID: resourceID,
			Status:     status,
			ReceivedAt: receivedAt,
			MaxRetries: 5,
			RawPayload: marshalJSON(payload),
		}

		// Set processed_at for terminal states
		if status == model.StatusCompleted || status == model.StatusFailed || status == model.StatusDLQ {
			processed := receivedAt.Add(time.Duration(rand.Float64()*2.9+0.1) * time.Second)
			event.ProcessedAt = &processed
		}

		// Set retry count
		switch status {
		case model.StatusFailed:
			event.RetryCount = rand.Intn(3) + 1
		case model.StatusDLQ:
			event.RetryCount = rand.Intn(3) + 3
		}

		// Set handler and worker for completed events
		if status == model.StatusCompleted {
			event.Handler = strings.ToUpper(strings.ReplaceAll(tmpl.Pattern, "*", "")) + "Handler"
		}
		if status != model.StatusPending {
			event.WorkerID = fmt.Sprintf("worker-%02d", rand.Intn(8)+1)
		}

		// Set error message for failed/DLQ
		if status == model.StatusFailed || status == model.StatusDLQ {
			event.ErrorMessage = "Simulated processing error"
		}

		eventsBatch = append(eventsBatch, event)

		// Generate logs
		logsBatch = append(logsBatch, model.EventLog{
			EventID:   event.ID,
			Action:    "received",
			Detail:    marshalJSON(map[string]interface{}{"source": tmpl.Source}),
			CreatedAt: receivedAt,
		})

		if status != model.StatusPending {
			logsBatch = append(logsBatch, model.EventLog{
				EventID:   event.ID,
				Action:    "processing",
				Detail:    marshalJSON(map[string]interface{}{"worker": event.WorkerID}),
				CreatedAt: receivedAt.Add(100 * time.Millisecond),
			})
		}

		switch status {
		case model.StatusCompleted:
			logsBatch = append(logsBatch, model.EventLog{
				EventID:   event.ID,
				Action:    "completed",
				Detail:    marshalJSON(map[string]interface{}{"result": "OK"}),
				CreatedAt: *event.ProcessedAt,
			})
		case model.StatusFailed:
			failTime := receivedAt.Add(time.Second)
			logsBatch = append(logsBatch, model.EventLog{
				EventID:   event.ID,
				Action:    "failed",
				Detail:    marshalJSON(map[string]interface{}{"error": event.ErrorMessage, "retry_count": event.RetryCount}),
				CreatedAt: failTime,
			})
		case model.StatusDLQ:
			failTime := receivedAt.Add(time.Second)
			logsBatch = append(logsBatch, model.EventLog{
				EventID:   event.ID,
				Action:    "failed",
				Detail:    marshalJSON(map[string]interface{}{"error": event.ErrorMessage, "retry_count": event.RetryCount}),
				CreatedAt: failTime,
			})
			logsBatch = append(logsBatch, model.EventLog{
				EventID:   event.ID,
				Action:    "dlq",
				Detail:    marshalJSON(map[string]interface{}{"error": event.ErrorMessage, "reason": "retries_exhausted"}),
				CreatedAt: failTime.Add(100 * time.Millisecond),
			})
		}

		// Flush batch
		if len(eventsBatch) >= batchSize {
			if err := db.Create(&eventsBatch).Error; err != nil {
				log.Fatalf("Failed to create events batch: %v", err)
			}
			if err := db.Create(&logsBatch).Error; err != nil {
				log.Fatalf("Failed to create logs batch: %v", err)
			}
			log.Printf("  📝 Written %d/%d...", i, total)
			eventsBatch = eventsBatch[:0]
			logsBatch = logsBatch[:0]
		}
	}

	// Flush remaining
	if len(eventsBatch) > 0 {
		if err := db.Create(&eventsBatch).Error; err != nil {
			log.Fatalf("Failed to create remaining events: %v", err)
		}
		if err := db.Create(&logsBatch).Error; err != nil {
			log.Fatalf("Failed to create remaining logs: %v", err)
		}
	}

	// ── Create EventHandlerConfig records ───────────────────────
	configs := []model.EventHandlerConfig{
		{
			Name:             "EchoHandler",
			EventTypePattern: "*",
			HandlerClass:     "handlers.internal.echo_handler.EchoHandler",
			Timeout:          60,
			MaxRetries:       5,
			IsActive:         true,
			Description:      "兜底 Handler",
		},
		{
			Name:             "EC2Handler",
			EventTypePattern: "aws.ec2.*",
			HandlerClass:     "handlers.aws.ec2_handler.EC2Handler",
			Timeout:          120,
			MaxRetries:       3,
			IsActive:         true,
			Description:      "AWS EC2 事件处理",
		},
		{
			Name:             "RDSHandler",
			EventTypePattern: "aws.rds.*",
			HandlerClass:     "handlers.aws.rds_handler.RDSHandler",
			Timeout:          120,
			MaxRetries:       3,
			IsActive:         true,
			Description:      "AWS RDS 事件处理",
		},
		{
			Name:             "S3Handler",
			EventTypePattern: "aws.s3.*",
			HandlerClass:     "handlers.aws.s3_handler.S3Handler",
			Timeout:          60,
			MaxRetries:       3,
			IsActive:         true,
			Description:      "AWS S3 事件处理",
		},
		{
			Name:             "GitHubHandler",
			EventTypePattern: "webhook.github.*",
			HandlerClass:     "handlers.webhook.github_handler.GitHubHandler",
			Timeout:          60,
			MaxRetries:       3,
			IsActive:         true,
			Description:      "GitHub Webhook 处理",
		},
	}
	for i := range configs {
		db.Create(&configs[i])
	}

	// ── Print stats ─────────────────────────────────────────────
	var count int64
	db.Model(&model.Event{}).Count(&count)
	log.Printf("✅ Done! Created %d events", count)
}

// ── Helpers ─────────────────────────────────────────────────────

func pickStatus(weights [5]int) string {
	statuses := [5]string{
		model.StatusCompleted,
		model.StatusFailed,
		model.StatusDLQ,
		model.StatusProcessing,
		model.StatusPending,
	}
	r := rand.Intn(100) + 1
	cumulative := 0
	for i, w := range weights {
		cumulative += w
		if r <= cumulative {
			return statuses[i]
		}
	}
	return model.StatusCompleted
}

func randomPastTime(hoursBack int) time.Time {
	now := time.Now()
	seconds := rand.Intn(hoursBack * 3600)
	return now.Add(-time.Duration(seconds) * time.Second)
}

func randomChoice(items []string) string {
	return items[rand.Intn(len(items))]
}

func randomChoiceInt(items []int) int {
	return items[rand.Intn(len(items))]
}

func marshalJSON(v interface{}) []byte {
	b, _ := json.Marshal(v)
	return b
}

func shortHex() string {
	return strings.ReplaceAll(uuid.New().String(), "-", "")
}
