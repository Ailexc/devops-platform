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

// EC2Handler handles "aws.ec2.*" events
type EC2Handler struct{}

// NewEC2Handler creates a new EC2Handler
func NewEC2Handler() types.Handler {
	return &EC2Handler{}
}

func (h *EC2Handler) Pattern() string { return "aws.ec2.*" }

func (h *EC2Handler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	delay := 0.3 + rand.Float64()*0.7 // 0.3–1.0s
	time.Sleep(time.Duration(delay * float64(time.Second)))

	state := "running"
	if v, ok := payload["state"].(string); ok && v != "" {
		state = v
	}
	instanceID := ""
	if v, ok := payload["instance_id"].(string); ok && v != "" {
		instanceID = v
	} else {
		instanceID = event.ResourceID
	}

	log.Printf("EC2 %s → %s (processed in %.2fs)", instanceID, state, delay)
	return types.HandlerResult{
		Success: true,
		Message: "EC2 instance " + instanceID + " state changed to " + state,
		Data: map[string]interface{}{
			"service":         "ec2",
			"instance_id":     instanceID,
			"state":           state,
			"region":          payload["region"],
			"processed_delay": delay,
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("aws.ec2.*", types.EventTypeMetadata{
		Category:    "aws",
		Icon:        "☁️",
		Pattern:     "aws.ec2.*",
		Description: "EC2 实例状态变更事件",
		Handler:     "EC2Handler",
		Events: []map[string]interface{}{
			{"type": "aws.ec2.state-change", "desc": "实例状态变更（启动/停止/重启）"},
			{"type": "aws.ec2.instance-created", "desc": "新 EC2 实例创建完成"},
			{"type": "aws.ec2.instance-terminated", "desc": "EC2 实例终止"},
			{"type": "aws.ec2.spot-instance-interrupted", "desc": "竞价实例中断通知"},
		},
		Schema: map[string]interface{}{
			"instance_id":   map[string]interface{}{"type": "string", "required": true, "desc": "EC2 实例 ID", "example": "i-0abcd1234"},
			"state":         map[string]interface{}{"type": "string", "required": true, "desc": "实例目标状态", "example": "running"},
			"region":        map[string]interface{}{"type": "string", "required": false, "default": "us-east-1", "desc": "AWS 区域", "example": "ap-northeast-1"},
			"instance_type": map[string]interface{}{"type": "string", "required": false, "desc": "实例规格", "example": "t3.medium"},
		},
		Example: map[string]interface{}{
			"instance_id":   "i-0abcd1234",
			"state":         "running",
			"region":        "ap-northeast-1",
			"instance_type": "t3.medium",
		},
	})
}
