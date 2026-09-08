package repository

import (
	"context"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"event-flow/internal/model"
)

type EventLogRepo struct {
	db *gorm.DB
}

func NewEventLogRepo(db *gorm.DB) *EventLogRepo {
	return &EventLogRepo{db: db}
}

// Create inserts a new event log record.
func (r *EventLogRepo) Create(ctx context.Context, log *model.EventLog) error {
	return r.db.WithContext(ctx).Create(log).Error
}

// ListByEventID returns all logs for a given event, ordered chronologically.
func (r *EventLogRepo) ListByEventID(ctx context.Context, eventID uuid.UUID) ([]model.EventLog, error) {
	var logs []model.EventLog
	err := r.db.WithContext(ctx).
		Where("event_id = ?", eventID).
		Order("created_at ASC").
		Find(&logs).Error
	return logs, err
}
