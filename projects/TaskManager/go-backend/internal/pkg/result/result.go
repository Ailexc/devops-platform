package result

import (
	"fmt"
	"time"
)

// Builder constructs a standardized execution result.
type Builder struct {
	Status    string                 `json:"status"`
	Summary   string                 `json:"summary"`
	Duration  string                 `json:"duration"`
	Logs      []string               `json:"logs"`
	Stats     []StatEntry            `json:"stats"`
	Artifacts []ArtifactEntry        `json:"artifacts"`
	Details   map[string]interface{} `json:"details"`
	startTime time.Time
}

// StatEntry represents a key-value statistic.
type StatEntry struct {
	Key   string `json:"key"`
	Label string `json:"label"`
	Value interface{} `json:"value"`
	Unit  string `json:"unit,omitempty"`
}

// ArtifactEntry represents a generated artifact.
type ArtifactEntry struct {
	Name string `json:"name"`
	Path string `json:"path,omitempty"`
	Kind string `json:"kind,omitempty"`
	Size int64  `json:"size,omitempty"`
}

// New creates a new result builder.
func New() *Builder {
	return &Builder{
		Status:    "success",
		Logs:      make([]string, 0),
		Stats:     make([]StatEntry, 0),
		Artifacts: make([]ArtifactEntry, 0),
		Details:   make(map[string]interface{}),
		startTime: time.Now(),
	}
}

// Log appends a timestamped log entry.
func (b *Builder) Log(text string) *Builder {
	b.Logs = append(b.Logs, fmt.Sprintf("%s %s", time.Now().Format("15:04:05"), text))
	return b
}

// AddStat adds a statistic entry.
func (b *Builder) AddStat(key, label string, value interface{}, unit string) *Builder {
	b.Stats = append(b.Stats, StatEntry{
		Key:   key,
		Label: label,
		Value: value,
		Unit:  unit,
	})
	return b
}

// AddArtifact adds an artifact entry.
func (b *Builder) AddArtifact(name, path, kind string, size int64) *Builder {
	b.Artifacts = append(b.Artifacts, ArtifactEntry{
		Name: name,
		Path: path,
		Kind: kind,
		Size: size,
	})
	return b
}

// SetDetail sets a detail field.
func (b *Builder) SetDetail(key string, value interface{}) *Builder {
	b.Details[key] = value
	return b
}

// Fail marks the result as failed.
func (b *Builder) Fail(errMsg string) *Builder {
	b.Status = "failed"
	b.Summary = errMsg
	return b
}

// Build finalizes the result and returns the JSON-serializable struct.
func (b *Builder) Build() map[string]interface{} {
	elapsed := time.Since(b.startTime)
	b.Duration = formatDuration(elapsed)

	if b.Summary == "" && b.Status == "success" {
		b.Summary = fmt.Sprintf("完成 (%s)", b.Duration)
	}

	return map[string]interface{}{
		"status":    b.Status,
		"summary":   b.Summary,
		"duration":  b.Duration,
		"logs":      b.Logs,
		"stats":     b.Stats,
		"artifacts": b.Artifacts,
		"details":   b.Details,
	}
}

func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.1fs", d.Seconds())
	}
 mins := int(d.Minutes())
	secs := int(d.Seconds()) % 60
	return fmt.Sprintf("%dm%02ds", mins, secs)
}
