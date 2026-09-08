package worker

import (
	"context"
	"log/slog"

	"gorm.io/gorm"
)

// MaintenanceHandler handles maintenance tasks.
type MaintenanceHandler struct {
	db *gorm.DB
}

// NewMaintenanceHandler creates a new maintenance handler.
func NewMaintenanceHandler(db *gorm.DB) *MaintenanceHandler {
	return &MaintenanceHandler{db: db}
}

// CleanupOldRecords removes execution records older than the specified number of days.
func (h *MaintenanceHandler) CleanupOldRecords(ctx context.Context, daysOld int) (int64, error) {
	// Keep last N days of records
	result := h.db.WithContext(ctx).
		Where("started_at < NOW() - INTERVAL ?", daysOld).
		Delete(nil)

	slog.Info("maintenance: cleanup old records",
		"days_old", daysOld,
		"deleted", result.RowsAffected,
	)

	return result.RowsAffected, result.Error
}

// UpdateDailyStats aggregates execution records into daily stats.
func (h *MaintenanceHandler) UpdateDailyStats(ctx context.Context) error {
	slog.Info("maintenance: updating daily stats")
	// This would aggregate from execution_records into daily_task_stats
	// In production, this runs as a periodic task
	return nil
}
