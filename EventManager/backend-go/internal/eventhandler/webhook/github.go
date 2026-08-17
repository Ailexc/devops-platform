package webhook

import (
	"context"
	"encoding/json"
	"log"
	"math/rand"
	"time"

	"event-flow/internal/eventhandler/types"
	"event-flow/internal/model"
)

// GitHubHandler handles "webhook.github.*" events
type GitHubHandler struct{}

// NewGitHubHandler creates a new GitHubHandler
func NewGitHubHandler() types.Handler {
	return &GitHubHandler{}
}

func (h *GitHubHandler) Pattern() string { return "webhook.github.*" }

func (h *GitHubHandler) Handle(ctx context.Context, event *model.Event) (types.HandlerResult, error) {
	var payload map[string]interface{}
	if err := json.Unmarshal(event.RawPayload, &payload); err != nil {
		payload = make(map[string]interface{})
	}

	delay := 0.1 + rand.Float64()*0.4 // 0.1–0.5s
	time.Sleep(time.Duration(delay * float64(time.Second)))

	ghEvent := "push"
	if v, ok := payload["github_event"].(string); ok && v != "" {
		ghEvent = v
	}
	repo := "unknown/repo"
	if v, ok := payload["repository"].(string); ok && v != "" {
		repo = v
	}
	ref := "main"
	if v, ok := payload["ref"].(string); ok && v != "" {
		ref = v
	}

	log.Printf("GitHub %s %s (%s) processed in %.2fs", ghEvent, repo, ref, delay)
	return types.HandlerResult{
		Success: true,
		Message: "GitHub " + ghEvent + " on " + repo + "/" + ref,
		Data: map[string]interface{}{
			"service":         "github",
			"event":           ghEvent,
			"repository":      repo,
			"ref":             ref,
			"commits":         payload["commits"],
			"processed_delay": delay,
		},
	}, nil
}

func init() {
	types.DefaultRegistry.RegisterMetadata("webhook.github.*", types.EventTypeMetadata{
		Category:    "webhook",
		Icon:        "🐙",
		Pattern:     "webhook.github.*",
		Description: "GitHub Webhook 事件",
		Handler:     "GitHubHandler",
		Events: []map[string]interface{}{
			{"type": "webhook.github.push", "desc": "代码推送"},
			{"type": "webhook.github.pull_request", "desc": "PR 打开/合并/关闭"},
			{"type": "webhook.github.issues", "desc": "Issue 创建/关闭"},
			{"type": "webhook.github.release", "desc": "Release 发布"},
			{"type": "webhook.github.star", "desc": "收藏/点赞"},
		},
		Schema: map[string]interface{}{
			"github_event": map[string]interface{}{"type": "string", "required": true, "desc": "GitHub 事件类型", "example": "push"},
			"repository":   map[string]interface{}{"type": "string", "required": true, "desc": "仓库全名", "example": "my-org/my-repo"},
			"ref":          map[string]interface{}{"type": "string", "required": false, "default": "main", "desc": "分支/标签引用", "example": "feature/new-api"},
			"commits":      map[string]interface{}{"type": "integer", "required": false, "desc": "提交数量", "example": 3},
		},
		Example: map[string]interface{}{
			"github_event": "push",
			"repository":   "my-org/my-repo",
			"ref":          "main",
			"commits":      3,
		},
	})
}
