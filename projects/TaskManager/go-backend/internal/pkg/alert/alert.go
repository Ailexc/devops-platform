package alert

import (
	"log/slog"
)

// Level represents alert severity.
type Level int

const (
	Info Level = iota
	Warning
	Critical
)

func (l Level) String() string {
	switch l {
	case Info:
		return "INFO"
	case Warning:
		return "WARNING"
	case Critical:
		return "CRITICAL"
	default:
		return "UNKNOWN"
	}
}

// Engine provides three-level alerting.
type Engine struct {
	// In a production system, this would send to Slack/PagerDuty/etc.
}

// NewEngine creates a new alert engine.
func NewEngine() *Engine {
	return &Engine{}
}

// Alert sends an alert at the given level.
func (e *Engine) Alert(level Level, module, message string, details map[string]interface{}) {
	switch level {
	case Critical:
		slog.Error("ALERT[CRITICAL]",
			"module", module,
			"message", message,
			"details", details,
		)
	case Warning:
		slog.Warn("ALERT[WARNING]",
			"module", module,
			"message", message,
			"details", details,
		)
	case Info:
		slog.Info("ALERT[INFO]",
			"module", module,
			"message", message,
			"details", details,
		)
	}
}
