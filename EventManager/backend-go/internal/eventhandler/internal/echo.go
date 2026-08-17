package internal

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"event-flow/internal/eventhandler/types"
	"event-flow/internal/model"
)

// EchoHandler handles echo.* events — mirrors Python's EchoHandler
type EchoHandler struct{}

// NewEchoHandler creates a new EchoHandler
func NewEchoHandler() types.Handler {
	return &EchoHandler{}
}

func (h *EchoHandler) Pattern() string { return "echo.*" }

func (h *EchoHandler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	// simulate_error → return transient error
	if v, ok := payload["simulate_error"].(bool); ok && v {
		return types.HandlerResult{
			Success: false,
			Message: "Simulated transient error",
		}, nil
	}

	// simulate_timeout → sleep 5s
	delay := time.Duration(500 * time.Millisecond)
	if v, ok := payload["simulate_timeout"].(bool); ok && v {
		delay = 5 * time.Second
	}

	time.Sleep(delay)

	log.Printf("EchoHandler processed event %s (type=%s)", event.ID, event.EventType)
	return types.HandlerResult{
		Success: true,
		Message: "Echo processed",
		Data: map[string]interface{}{
			"echo":       true,
			"event_type": event.EventType,
			"source":     event.Source,
			"delay":      delay.Seconds(),
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("echo.*", types.EventTypeMetadata{
		Category:    "echo",
		Icon:        "🔊",
		Pattern:     "echo.*",
		Description: "回显 Handler - 用于 Demo 测试",
		Handler:     "EchoHandler",
		Events: []map[string]interface{}{
			{"type": "echo.test", "desc": "基础回显测试"},
			{"type": "echo.error", "desc": "模拟处理失败（测试重试/DLQ）"},
			{"type": "echo.timeout", "desc": "模拟处理超时"},
		},
		Schema: map[string]interface{}{
			"message":          map[string]interface{}{"type": "string", "required": false, "desc": "回显消息", "example": "Hello World"},
			"simulate_error":   map[string]interface{}{"type": "boolean", "required": false, "desc": "设为 true 模拟处理失败", "example": false},
			"simulate_timeout": map[string]interface{}{"type": "boolean", "required": false, "desc": "设为 true 模拟超时", "example": false},
		},
		Example: map[string]interface{}{
			"message":          "Hello World",
			"simulate_error":   false,
			"simulate_timeout": false,
		},
	})
}
