package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"event-flow/internal/eventhandler"
	"event-flow/internal/model"
)

// dbHolder holds the GORM DB reference used by the worker.
// It is set once at startup via SetDB.
var dbHolder *gorm.DB

// SetDB configures the database connection for the worker.
func SetDB(db *gorm.DB) {
	dbHolder = db
}

// EventPayload is the JSON payload of an asynq task.
type EventPayload struct {
	EventID string `json:"event_id"`
}

// ProcessEvent is the core event processing logic.
// It uses SELECT FOR UPDATE + NOWAIT to ensure at-most-once processing.
func ProcessEvent(ctx context.Context, eventID string) error {
	if dbHolder == nil {
		return fmt.Errorf("worker: database not initialised")
	}

	id, err := uuid.Parse(eventID)
	if err != nil {
		return fmt.Errorf("worker: invalid event ID %q: %w", eventID, err)
	}

	// ── Begin transaction ────────────────────────────────────────
	tx := dbHolder.WithContext(ctx).Begin()
	if tx.Error != nil {
		return fmt.Errorf("worker: begin tx: %w", tx.Error)
	}

	// ── Lock the event row (SELECT … FOR UPDATE NOWAIT) ─────────
	var event model.Event
	err = tx.Clauses(clause.Locking{Strength: "UPDATE", Options: "NOWAIT"}).
		Where("id = ?", id).
		First(&event).Error
	if err != nil {
		tx.Rollback()
		if err == gorm.ErrRecordNotFound {
			return fmt.Errorf("worker: event %s not found", eventID)
		}
		return fmt.Errorf("worker: lock event: %w", err)
	}

	// ── Idempotency check ───────────────────────────────────────
	// Skip if already processing or completed
	switch event.Status {
	case model.StatusProcessing, model.StatusCompleted:
		tx.Rollback()
		log.Printf("Worker: skipping event %s (status=%s)", eventID, event.Status)
		return nil
	case model.StatusDLQ:
		// Allow DLQ replay
	}

	// ── Mark as processing ──────────────────────────────────────
	now := time.Now()
	workerID := fmt.Sprintf("worker-%s", hostname())
	err = tx.Model(&event).Updates(map[string]interface{}{
		"status":    model.StatusProcessing,
		"worker_id": workerID,
	}).Error
	if err != nil {
		tx.Rollback()
		return fmt.Errorf("worker: mark processing: %w", err)
	}

	// ── Write PROCESSING log ────────────────────────────────────
	processingLog := model.EventLog{
		EventID:   id,
		Action:    "processing",
		Detail:    mustMarshal(map[string]interface{}{"worker": workerID}),
		CreatedAt: now,
	}
	if err := tx.Create(&processingLog).Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("worker: write processing log: %w", err)
	}

	if err := tx.Commit().Error; err != nil {
		return fmt.Errorf("worker: commit tx: %w", err)
	}

	// ── Resolve handler ─────────────────────────────────────────
	handler, err := eventhandler.DefaultRegistry.Resolve(event.EventType)
	if err != nil {
		return handleFailure(ctx, &event, fmt.Sprintf("handler not found: %s", event.EventType))
	}
	handlerName := fmt.Sprintf("%T", handler)
	// Strip package prefix — e.g. "*eventhandler.internal.EchoHandler" → "EchoHandler"
	if idx := strings.LastIndex(handlerName, "."); idx >= 0 {
		handlerName = handlerName[idx+1:]
	}

	// ── Call handler ────────────────────────────────────────────
	result, handlerErr := handler.Handle(ctx, &event)

	// ── On success ──────────────────────────────────────────────
	if handlerErr == nil && result.Success {
		return handleSuccess(ctx, &event, result, handlerName)
	}

	// ── On failure ──────────────────────────────────────────────
	errMsg := result.Message
	if handlerErr != nil {
		errMsg = handlerErr.Error()
	}
	return handleFailure(ctx, &event, errMsg)
}

// handleSuccess marks the event as completed and writes a COMPLETED log.
func handleSuccess(ctx context.Context, event *model.Event, result eventhandler.HandlerResult, handlerName string) error {
	now := time.Now()
	db := dbHolder.WithContext(ctx)

	err := db.Model(event).Updates(map[string]interface{}{
		"status":       model.StatusCompleted,
		"handler":      handlerName,
		"processed_at": now,
	}).Error
	if err != nil {
		return fmt.Errorf("worker: mark completed: %w", err)
	}

	logEntry := model.EventLog{
		EventID:   event.ID,
		Action:    "completed",
		Detail:    mustMarshal(map[string]interface{}{"result": result.Message}),
		CreatedAt: now,
	}
	if err := db.Create(&logEntry).Error; err != nil {
		return fmt.Errorf("worker: write completed log: %w", err)
	}

	log.Printf("Worker: event %s completed ✓", event.ID)
	return nil
}

// handleFailure handles retry logic and eventual DLQ placement.
func handleFailure(ctx context.Context, event *model.Event, errMsg string) error {
	now := time.Now()
	db := dbHolder.WithContext(ctx)

	event.RetryCount++
	event.ErrorMessage = errMsg

	// Check retries exhausted → DLQ
	if event.RetryCount >= event.MaxRetries {
		err := db.Model(event).Updates(map[string]interface{}{
			"status":        model.StatusDLQ,
			"retry_count":   event.RetryCount,
			"error_message": errMsg,
			"processed_at":  now,
		}).Error
		if err != nil {
			return fmt.Errorf("worker: mark DLQ: %w", err)
		}

		dlqLog := model.EventLog{
			EventID:   event.ID,
			Action:    "dlq",
			Detail:    mustMarshal(map[string]interface{}{"error": errMsg, "reason": "retries_exhausted"}),
			CreatedAt: now,
		}
		if err := db.Create(&dlqLog).Error; err != nil {
			return fmt.Errorf("worker: write DLQ log: %w", err)
		}

		log.Printf("Worker: event %s → DLQ (retries exhausted)", event.ID)
		return nil
	}

	// Still has retries → mark failed, schedule retry
	err := db.Model(event).Updates(map[string]interface{}{
		"status":        model.StatusFailed,
		"retry_count":   event.RetryCount,
		"error_message": errMsg,
	}).Error
	if err != nil {
		return fmt.Errorf("worker: mark failed: %w", err)
	}

	failLog := model.EventLog{
		EventID:   event.ID,
		Action:    "failed",
		Detail:    mustMarshal(map[string]interface{}{"error": errMsg, "retry_count": event.RetryCount}),
		CreatedAt: now,
	}
	if err := db.Create(&failLog).Error; err != nil {
		return fmt.Errorf("worker: write failed log: %w", err)
	}

	delay := BackoffDelay(event.RetryCount)
	log.Printf("Worker: event %s failed (retry %d/%d in %v)", event.ID, event.RetryCount, event.MaxRetries, delay)

	// Schedule retry by re-enqueuing after the delay
	// In a production system you would use asynq's ProcessAt option.
	// For simplicity we use a goroutine with time.Sleep.
	go func() {
		time.Sleep(delay)
		retryCtx := context.Background()
		// Reset to pending for re-processing
		_ = dbHolder.WithContext(retryCtx).Model(&model.Event{}).
			Where("id = ?", event.ID).
			Update("status", model.StatusPending).Error
		log.Printf("Worker: event %s re-queued for retry", event.ID)
	}()

	return nil
}

// mustMarshal is a helper that panics on marshal errors (should never happen).
func mustMarshal(v interface{}) []byte {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err)
	}
	return b
}

// hostname returns the OS hostname, used for worker identification.
func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}
