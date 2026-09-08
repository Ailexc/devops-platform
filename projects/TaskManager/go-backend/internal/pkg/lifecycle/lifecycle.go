package lifecycle

import (
	"encoding/json"
	"fmt"
	"time"

	"gorm.io/gorm"
)

// Event represents a single lifecycle event.
type Event struct {
	Timestamp string `json:"ts"`
	Event     string `json:"event"`
	Label     string `json:"label"`
	Detail    string `json:"detail,omitempty"`
	Icon      string `json:"icon,omitempty"`
}

// Tracker manages lifecycle events for an execution record.
type Tracker struct {
	db     *gorm.DB
	recordID int64
}

// NewTracker creates a new lifecycle tracker for a given execution record.
func NewTracker(db *gorm.DB, recordID int64) *Tracker {
	return &Tracker{db: db, recordID: recordID}
}

// Append adds a lifecycle event to the execution record.
func (t *Tracker) Append(event, label, detail string) error {
	icons := map[string]string{
		"created":   "📥",
		"running":   "🔄",
		"completed": "✅",
		"failed":    "❌",
		"retrying":  "🔁",
		"timeout":   "⏰",
		"cancelled": "🚫",
	}

	evt := Event{
		Timestamp: time.Now().Format("15:04:05"),
		Event:     event,
		Label:     label,
		Detail:    detail,
		Icon:      icons[event],
	}

	// Read current events, append, and update
	var rawJSON []byte
	result := t.db.Raw(
		"SELECT lifecycle_events FROM execution_records WHERE id = ?", t.recordID,
	).Scan(&rawJSON)
	if result.Error != nil {
		return result.Error
	}

	var current []Event
	if len(rawJSON) > 0 {
		_ = json.Unmarshal(rawJSON, &current)
	}
	if current == nil {
		current = make([]Event, 0)
	}
	current = append(current, evt)

	eventsJSON, err := json.Marshal(current)
	if err != nil {
		return fmt.Errorf("failed to marshal lifecycle events: %w", err)
	}

	return t.db.Exec(
		"UPDATE execution_records SET lifecycle_events = ? WHERE id = ?",
		string(eventsJSON), t.recordID,
	).Error
}
