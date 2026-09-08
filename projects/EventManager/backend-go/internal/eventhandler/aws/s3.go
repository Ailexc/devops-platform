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

// S3Handler handles "aws.s3.*" events
type S3Handler struct{}

// NewS3Handler creates a new S3Handler
func NewS3Handler() types.Handler {
	return &S3Handler{}
}

func (h *S3Handler) Pattern() string { return "aws.s3.*" }

func (h *S3Handler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	delay := 0.2 + rand.Float64()*0.6 // 0.2–0.8s
	time.Sleep(time.Duration(delay * float64(time.Second)))

	bucket := "unknown-bucket"
	if v, ok := payload["bucket"].(string); ok && v != "" {
		bucket = v
	}
	objKey := "unknown"
	if v, ok := payload["object_key"].(string); ok && v != "" {
		objKey = v
	}
	action := "PUT"
	if v, ok := payload["action"].(string); ok && v != "" {
		action = v
	}

	log.Printf("S3 %s %s %s (processed in %.2fs)", bucket, action, objKey, delay)
	return types.HandlerResult{
		Success: true,
		Message: "S3 " + action + " " + bucket + "/" + objKey,
		Data: map[string]interface{}{
			"service":         "s3",
			"bucket":          bucket,
			"object_key":      objKey,
			"action":          action,
			"size":            payload["size"],
			"processed_delay": delay,
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("aws.s3.*", types.EventTypeMetadata{
		Category:    "aws",
		Icon:        "🪣",
		Pattern:     "aws.s3.*",
		Description: "S3 对象操作事件",
		Handler:     "S3Handler",
		Events: []map[string]interface{}{
			{"type": "aws.s3.object-created", "desc": "对象上传/创建"},
			{"type": "aws.s3.object-deleted", "desc": "对象删除"},
			{"type": "aws.s3.object-restored", "desc": "对象从归档恢复"},
			{"type": "aws.s3.bucket-created", "desc": "新存储桶创建"},
		},
		Schema: map[string]interface{}{
			"bucket":     map[string]interface{}{"type": "string", "required": true, "desc": "S3 存储桶名称", "example": "my-app-data"},
			"object_key": map[string]interface{}{"type": "string", "required": true, "desc": "对象键值（路径）", "example": "uploads/2026/07/report.pdf"},
			"action":     map[string]interface{}{"type": "string", "required": true, "desc": "操作类型", "example": "PUT"},
			"size":       map[string]interface{}{"type": "integer", "required": false, "desc": "对象大小（字节）", "example": 1048576},
		},
		Example: map[string]interface{}{
			"bucket":     "my-app-data",
			"object_key": "uploads/2026/07/report.pdf",
			"action":     "PUT",
			"size":       1048576,
		},
	})
}
