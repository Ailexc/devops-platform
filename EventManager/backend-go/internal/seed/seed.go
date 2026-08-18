// Package seed 提供 EventManager Go 栈的统一幂等种子逻辑。
//
// 设计目标（对齐"启动时幂等种子"标准，替换独立 go-seed 容器）：
//   - go-api 启动时调用 EnsureDemoData，空库自动灌入演示数据，非空跳过（不覆盖真实/运行数据）
//   - Handler 配置用 FirstOrCreate 幂等同步
//   - 需要强制重灌时（make reset / 手动），先清空库或传 force=true
package seed

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strings"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"event-flow/internal/model"
)

// DefaultTotal 默认演示事件数量
const DefaultTotal = 1000

// EventTemplate 事件生成模板（对齐 Python seed_data.py 模板）
type EventTemplate struct {
	Pattern       string
	Source        string
	Events        []EventInfo
	StatusWeights [5]int // completed, failed, dlq, processing, pending
	PayloadFn     func() map[string]interface{}
}

// EventInfo 模板内事件类型
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
				"bucket": randomChoice([]string{"prod-logs", "backup-archive", "data-lake", "media"}),
				"action": randomChoice([]string{"PUT", "POST", "DELETE", "COPY"}),
				"region": randomChoice([]string{"us-east-1", "eu-west-1", "ap-southeast-1"}),
			}
		},
	},
	{
		Pattern:       "webhook.github.*",
		Source:        "github",
		StatusWeights: [5]int{70, 12, 6, 6, 6},
		Events: []EventInfo{
			{Type: "webhook.github.push", Resources: []string{"repo-"}},
			{Type: "webhook.github.pull_request", Resources: []string{"repo-"}},
			{Type: "webhook.github.issue", Resources: []string{"repo-"}},
		},
		PayloadFn: func() map[string]interface{} {
			return map[string]interface{}{
				"repo":    fmt.Sprintf("org/%s", randomChoice([]string{"infra", "platform", "app", "data"})),
				"actor":   randomChoice([]string{"alice", "bob", "carol", "devops-bot"}),
				"branch":  randomChoice([]string{"main", "develop", "release/v1.2", "feature/ci"}),
				"simulate_error": rand.Intn(10) == 0,
			}
		},
	},
}

// defaultHandlerConfigs 需要幂等确保存在的 Handler 配置
var defaultHandlerConfigs = []model.EventHandlerConfig{
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

// EnsureDemoData 启动时幂等种子：
//   - Handler 配置：按 Name FirstOrCreate（存在即保留，不覆盖）
//   - 事件数据：表为空时灌入 total 条演示事件 + 日志；表非空且未 force 时跳过
//   - force=true 时先 TRUNCATE 再重灌（用于手动强制重灌）
func EnsureDemoData(db *gorm.DB, total int, force bool) error {
	// ── 1) Handler 配置（幂等）────────────────────────────
	for i := range defaultHandlerConfigs {
		cfg := defaultHandlerConfigs[i]
		var existing model.EventHandlerConfig
		err := db.Where("name = ?", cfg.Name).First(&existing).Error
		if err == gorm.ErrRecordNotFound {
			if err := db.Create(&cfg).Error; err != nil {
				return fmt.Errorf("seed: 创建 handler 配置 %s 失败: %w", cfg.Name, err)
			}
			log.Printf("  ✅ 创建 Handler 配置 %s", cfg.Name)
		} else if err != nil {
			return fmt.Errorf("seed: 查询 handler 配置 %s 失败: %w", cfg.Name, err)
		}
	}

	// ── 2) 事件数据（空库首灌 / force 重灌）───────────────
	var count int64
	if err := db.Model(&model.Event{}).Count(&count).Error; err != nil {
		return fmt.Errorf("seed: 统计事件数失败: %w", err)
	}
	if count > 0 && !force {
		log.Printf("  ℹ️  api_event 已有 %d 条数据，跳过演示数据（幂等）", count)
		return nil
	}

	if force {
		log.Println("  🗑️  强制重灌：清空现有事件数据")
		if err := db.Exec("TRUNCATE api_eventlog CASCADE").Error; err != nil {
			return fmt.Errorf("seed: 清空日志失败: %w", err)
		}
		if err := db.Exec("TRUNCATE api_event CASCADE").Error; err != nil {
			return fmt.Errorf("seed: 清空事件失败: %w", err)
		}
	}

	log.Printf("🌱 生成 %d 条模拟事件...", total)
	if err := generateEvents(db, total); err != nil {
		return err
	}

	var final int64
	db.Model(&model.Event{}).Count(&final)
	log.Printf("✅ seed 完成！api_event 共 %d 条", final)
	return nil
}

// generateEvents 批量生成模拟事件 + 日志
func generateEvents(db *gorm.DB, total int) error {
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

		// terminal 状态设置 processed_at
		if status == model.StatusCompleted || status == model.StatusFailed || status == model.StatusDLQ {
			processed := receivedAt.Add(time.Duration(rand.Float64()*2.9+0.1) * time.Second)
			event.ProcessedAt = &processed
		}

		// 重试次数
		switch status {
		case model.StatusFailed:
			event.RetryCount = rand.Intn(3) + 1
		case model.StatusDLQ:
			event.RetryCount = rand.Intn(3) + 3
		}

		// completed 事件带 Handler，非 pending 事件带 Worker
		if status == model.StatusCompleted {
			event.Handler = strings.ToUpper(strings.ReplaceAll(tmpl.Pattern, "*", "")) + "Handler"
		}
		if status != model.StatusPending {
			event.WorkerID = fmt.Sprintf("worker-%02d", rand.Intn(8)+1)
		}

		// failed/DLQ 错误信息
		if status == model.StatusFailed || status == model.StatusDLQ {
			event.ErrorMessage = "Simulated processing error"
		}

		eventsBatch = append(eventsBatch, event)

		// 日志
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

		// 批量 flush
		if len(eventsBatch) >= batchSize {
			if err := db.Create(&eventsBatch).Error; err != nil {
				return fmt.Errorf("seed: 批量写事件失败: %w", err)
			}
			if err := db.Create(&logsBatch).Error; err != nil {
				return fmt.Errorf("seed: 批量写日志失败: %w", err)
			}
			log.Printf("  📝 已写入 %d/%d", i, total)
			eventsBatch = eventsBatch[:0]
			logsBatch = logsBatch[:0]
		}
	}

	if len(eventsBatch) > 0 {
		if err := db.Create(&eventsBatch).Error; err != nil {
			return fmt.Errorf("seed: 写剩余事件失败: %w", err)
		}
		if err := db.Create(&logsBatch).Error; err != nil {
			return fmt.Errorf("seed: 写剩余日志失败: %w", err)
		}
	}
	return nil
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
