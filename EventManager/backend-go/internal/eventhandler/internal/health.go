package internal

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"event-flow/internal/eventhandler/types"
	"event-flow/internal/model"
)

// HealthCheckHandler handles "internal.health" events
type HealthCheckHandler struct{}

// NewHealthCheckHandler creates a new HealthCheckHandler
func NewHealthCheckHandler() types.Handler {
	return &HealthCheckHandler{}
}

func (h *HealthCheckHandler) Pattern() string { return "internal.health" }

func (h *HealthCheckHandler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	time.Sleep(50 * time.Millisecond)

	checkType := "ping"
	if v, ok := payload["check"].(string); ok && v != "" {
		checkType = v
	}
	component := "api"
	if v, ok := payload["component"].(string); ok && v != "" {
		component = v
	}

	log.Printf("Health check %s/%s OK", component, checkType)
	return types.HandlerResult{
		Success: true,
		Message: component + " " + checkType + " OK",
		Data: map[string]interface{}{
			"service":   "health",
			"component": component,
			"check":     checkType,
			"status":    "healthy",
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("internal.health", types.EventTypeMetadata{
		Category:    "internal",
		Icon:        "💚",
		Pattern:     "internal.health",
		Description: "内部健康检查事件",
		Handler:     "HealthCheckHandler",
		Events: []map[string]interface{}{
			{"type": "internal.health", "desc": "定时健康检查"},
		},
		Schema: map[string]interface{}{
			"component": map[string]interface{}{"type": "string", "required": false, "default": "api", "desc": "被检查的组件名", "example": "celery-worker"},
			"check":     map[string]interface{}{"type": "string", "required": false, "default": "ping", "desc": "检查类型", "example": "db-connectivity"},
		},
		Example: map[string]interface{}{
			"component": "celery-worker",
			"check":     "ping",
		},
	})
}
