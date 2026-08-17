package aws

import (
	"context"
	"encoding/json"
	"log"
	"math/rand"
	"time"

	"event-flow/internal/eventhandler/types"
	"event-flow/internal/model"
)

// RDSHandler handles "aws.rds.*" events
type RDSHandler struct{}

// NewRDSHandler creates a new RDSHandler
func NewRDSHandler() types.Handler {
	return &RDSHandler{}
}

func (h *RDSHandler) Pattern() string { return "aws.rds.*" }

func (h *RDSHandler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	delay := 1.0 + rand.Float64()*2.0 // 1.0–3.0s
	time.Sleep(time.Duration(delay * float64(time.Second)))

	dbID := ""
	if v, ok := payload["db_instance"].(string); ok && v != "" {
		dbID = v
	} else {
		dbID = event.ResourceID
	}
	category := "notification"
	if v, ok := payload["category"].(string); ok && v != "" {
		category = v
	}

	log.Printf("RDS %s [%s] (processed in %.2fs)", dbID, category, delay)
	return types.HandlerResult{
		Success: true,
		Message: "RDS " + dbID + " event processed",
		Data: map[string]interface{}{
			"service":         "rds",
			"db_instance":     dbID,
			"category":        category,
			"region":          payload["region"],
			"processed_delay": delay,
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("aws.rds.*", types.EventTypeMetadata{
		Category:    "aws",
		Icon:        "🗄️",
		Pattern:     "aws.rds.*",
		Description: "RDS 数据库事件",
		Handler:     "RDSHandler",
		Events: []map[string]interface{}{
			{"type": "aws.rds.instance-created", "desc": "新 RDS 实例创建"},
			{"type": "aws.rds.backup-completed", "desc": "自动备份完成"},
			{"type": "aws.rds.failover", "desc": "主备故障转移"},
			{"type": "aws.rds.instance-resized", "desc": "实例规格扩缩容"},
			{"type": "aws.rds.maintenance", "desc": "维护事件"},
		},
		Schema: map[string]interface{}{
			"db_instance": map[string]interface{}{"type": "string", "required": true, "desc": "RDS 实例标识符", "example": "db-prod-01"},
			"category":    map[string]interface{}{"type": "string", "required": true, "desc": "事件分类", "example": "backup"},
			"region":      map[string]interface{}{"type": "string", "required": false, "default": "us-east-1", "desc": "AWS 区域", "example": "eu-west-1"},
			"storage":     map[string]interface{}{"type": "integer", "required": false, "desc": "存储容量 GB", "example": 500},
		},
		Example: map[string]interface{}{
			"db_instance": "db-prod-01",
			"category":    "backup",
			"region":      "eu-west-1",
			"storage":     500,
		},
	})
}
