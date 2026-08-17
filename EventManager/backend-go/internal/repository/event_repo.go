package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"event-flow/internal/model"
)

// ListParams holds pagination and filter parameters for listing events.
type ListParams struct {
	Page       int    `json:"page"`
	PageSize   int    `json:"page_size"`
	Status     string `json:"status"`
	EventType  string `json:"event_type"`
	Source     string `json:"source"`
	Search     string `json:"search"`
	SearchField string `json:"search_field"`
}

// HourlyThroughput holds per-hour aggregated throughput stats.
type HourlyThroughput struct {
	Hour      string `json:"hour"`
	Total     int    `json:"total"`
	Completed int    `json:"completed"`
	Failed    int    `json:"failed"`
	Other     int    `json:"other"`
}

type EventRepo struct {
	db *gorm.DB
}

func NewEventRepo(db *gorm.DB) *EventRepo {
	return &EventRepo{db: db}
}

// Create inserts a new event record.
func (r *EventRepo) Create(ctx context.Context, event *model.Event) error {
	return r.db.WithContext(ctx).Create(event).Error
}

// GetByID retrieves an event by its UUID, eagerly loading its Logs.
func (r *EventRepo) GetByID(ctx context.Context, id uuid.UUID) (*model.Event, error) {
	var event model.Event
	err := r.db.WithContext(ctx).
		Preload("Logs").
		Where("id = ?", id).
		First(&event).Error
	if err != nil {
		return nil, err
	}
	return &event, nil
}

// GetByIDForUpdate retrieves an event with a row-level lock (SELECT ... FOR UPDATE NOWAIT).
// The caller should pass the transaction they want the lock acquired in.
func (r *EventRepo) GetByIDForUpdate(ctx context.Context, id uuid.UUID, tx *gorm.DB) (*model.Event, error) {
	var event model.Event
	err := tx.WithContext(ctx).
		Clauses(clause.Locking{Strength: "UPDATE", Options: "NOWAIT"}).
		Where("id = ?", id).
		First(&event).Error
	if err != nil {
		return nil, err
	}
	return &event, nil
}

// List returns paginated, filtered events.
func (r *EventRepo) List(ctx context.Context, params ListParams) ([]model.Event, int64, error) {
	var events []model.Event
	var total int64

	q := r.db.WithContext(ctx).Model(&model.Event{})

	// Filters
	if params.Status != "" {
		q = q.Where("status = ?", params.Status)
	}
	if params.EventType != "" {
		q = q.Where("event_type = ?", params.EventType)
	}
	if params.Source != "" {
		q = q.Where("source = ?", params.Source)
	}

	// Search
	if params.Search != "" {
		q = r.applySearch(q, params.Search, params.SearchField)
	}

	// Count total before pagination
	if err := q.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// Pagination defaults
	page := params.Page
	if page < 1 {
		page = 1
	}
	pageSize := params.PageSize
	if pageSize < 1 {
		pageSize = 20
	}
	offset := (page - 1) * pageSize

	err := q.
		Order("received_at DESC").
		Offset(offset).
		Limit(pageSize).
		Find(&events).Error
	if err != nil {
		return nil, 0, err
	}

	return events, total, nil
}

// applySearch adds search conditions based on the field.
func (r *EventRepo) applySearch(q *gorm.DB, search string, field string) *gorm.DB {
	like := "%" + search + "%"

	switch field {
	case "id":
		q = q.Where("id::text ILIKE ?", like)
	case "event_type":
		q = q.Where("event_type ILIKE ?", like)
	case "resource_id":
		q = q.Where("resource_id ILIKE ?", like)
	case "batch_id":
		q = q.Where("raw_payload->>'batch_id' ILIKE ?", like)
	case "all", "":
		q = q.Where(
			"id::text ILIKE ? OR event_type ILIKE ? OR resource_id ILIKE ? OR source ILIKE ? OR raw_payload->>'batch_id' ILIKE ?",
			like, like, like, like, like,
		)
	default:
		// Unknown field – fall back to all-field search
		q = q.Where(
			"id::text ILIKE ? OR event_type ILIKE ? OR resource_id ILIKE ? OR source ILIKE ? OR raw_payload->>'batch_id' ILIKE ?",
			like, like, like, like, like,
		)
	}
	return q
}

// Update saves all changed fields of the event.
func (r *EventRepo) Update(ctx context.Context, event *model.Event) error {
	return r.db.WithContext(ctx).Save(event).Error
}

// UpdateFields updates specific columns for an event by ID.
func (r *EventRepo) UpdateFields(ctx context.Context, id uuid.UUID, fields map[string]interface{}) error {
	return r.db.WithContext(ctx).
		Model(&model.Event{}).
		Where("id = ?", id).
		Updates(fields).Error
}

// BatchCreate inserts multiple events in a single transaction.
func (r *EventRepo) BatchCreate(ctx context.Context, events []model.Event) error {
	if len(events) == 0 {
		return nil
	}
	return r.db.WithContext(ctx).Create(&events).Error
}

// ReplayDLQ resets DLQ events back to pending state so they can be retried.
func (r *EventRepo) ReplayDLQ(ctx context.Context, eventIDs []uuid.UUID) (int64, error) {
	if len(eventIDs) == 0 {
		return 0, nil
	}
	result := r.db.WithContext(ctx).
		Model(&model.Event{}).
		Where("id IN ? AND status = ?", eventIDs, "dlq").
		Updates(map[string]interface{}{
			"status":       "pending",
			"retry_count":  0,
			"error_message": "",
		})
	return result.RowsAffected, result.Error
}

// CountByStatus returns the number of events grouped by status.
func (r *EventRepo) CountByStatus(ctx context.Context) (map[string]int64, error) {
	type statusCount struct {
		Status string
		Count  int64
	}
	var rows []statusCount

	err := r.db.WithContext(ctx).
		Model(&model.Event{}).
		Select("status, count(*) as count").
		Group("status").
		Scan(&rows).Error
	if err != nil {
		return nil, err
	}

	result := make(map[string]int64, len(rows))
	for _, row := range rows {
		result[row.Status] = row.Count
	}
	return result, nil
}

// Count returns the total number of events.
func (r *EventRepo) Count(ctx context.Context) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Model(&model.Event{}).Count(&count).Error
	return count, err
}

// GetRecentStats returns recent total, success count, and average duration for completed events.
func (r *EventRepo) GetRecentStats(ctx context.Context, since time.Time) (recentTotal int64, recentSuccess int64, avgDuration *float64, err error) {
	base := r.db.WithContext(ctx).Model(&model.Event{}).Where("received_at >= ?", since)

	// Total since
	if err = base.Count(&recentTotal).Error; err != nil {
		return
	}

	// Completed count
	if err = base.Where("status = ?", "completed").Count(&recentSuccess).Error; err != nil {
		return
	}

	// Average duration for completed events
	type avgResult struct {
		Avg float64
	}
	var ar avgResult
	err = r.db.WithContext(ctx).
		Model(&model.Event{}).
		Select("AVG(EXTRACT(EPOCH FROM (processed_at - received_at))) as avg").
		Where("status = ? AND received_at >= ? AND processed_at IS NOT NULL", "completed", since).
		Scan(&ar).Error
	if err != nil {
		return
	}
	avgDuration = &ar.Avg
	return
}

// GetHourlyThroughput returns per-hour event throughput broken down by status.
func (r *EventRepo) GetHourlyThroughput(ctx context.Context, since time.Time) ([]HourlyThroughput, error) {
	type hourlyRow struct {
		Hour   string
		Status string
		Count  int
	}
	var rows []hourlyRow

	err := r.db.WithContext(ctx).
		Model(&model.Event{}).
		Select("date_trunc('hour', received_at) as hour, status, count(*) as count").
		Where("received_at >= ?", since).
		Group("date_trunc('hour', received_at), status").
		Order("hour ASC").
		Scan(&rows).Error
	if err != nil {
		return nil, err
	}

	// Pivot rows into HourlyThroughput structs
	bucketMap := make(map[string]*HourlyThroughput)
	var order []string

	for _, row := range rows {
		hourStr := row.Hour
		b, ok := bucketMap[hourStr]
		if !ok {
			b = &HourlyThroughput{Hour: hourStr}
			bucketMap[hourStr] = b
			order = append(order, hourStr)
		}
		b.Total += row.Count
		switch row.Status {
		case "completed":
			b.Completed += row.Count
		case "failed", "dlq":
			b.Failed += row.Count
		default:
			b.Other += row.Count
		}
	}

	result := make([]HourlyThroughput, 0, len(order))
	for _, h := range order {
		result = append(result, *bucketMap[h])
	}
	return result, nil
}

// GetRecentFailures returns the most recent failed/DLQ events.
func (r *EventRepo) GetRecentFailures(ctx context.Context, limit int) ([]model.Event, error) {
	if limit <= 0 {
		limit = 10
	}
	var events []model.Event
	err := r.db.WithContext(ctx).
		Where("status IN ?", []string{"failed", "dlq"}).
		Order("received_at DESC").
		Limit(limit).
		Find(&events).Error
	return events, err
}

// GetPendingCount returns the number of events with status 'pending'.
func (r *EventRepo) GetPendingCount(ctx context.Context) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).
		Model(&model.Event{}).
		Where("status = ?", "pending").
		Count(&count).Error
	return count, err
}

// ListByStatus returns the count of events matching any of the given statuses.
func (r *EventRepo) ListByStatus(ctx context.Context, statuses []string) (int64, error) {
	if len(statuses) == 0 {
		return 0, nil
	}
	var count int64
	err := r.db.WithContext(ctx).
		Model(&model.Event{}).
		Where("status IN ?", statuses).
		Count(&count).Error
	return count, err
}

// helper – unused, kept for reference
var _ = fmt.Sprintf
