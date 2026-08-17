package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/datatypes"

	"event-flow/internal/api/dto"
	"event-flow/internal/model"
	"event-flow/internal/repository"
	"event-flow/internal/worker"
)

// EventsHandler holds dependencies for event CRUD endpoints.
type EventsHandler struct {
	EventRepo  *repository.EventRepo
	LogRepo    *repository.EventLogRepo
	Dispatcher worker.Dispatcher
}

// NewEventsHandler creates a new EventsHandler.
func NewEventsHandler(eventRepo *repository.EventRepo, logRepo *repository.EventLogRepo, dispatcher worker.Dispatcher) *EventsHandler {
	return &EventsHandler{
		EventRepo:  eventRepo,
		LogRepo:    logRepo,
		Dispatcher: dispatcher,
	}
}

// CreateEvent handles POST /api/v1/events
func (h *EventsHandler) CreateEvent(c *gin.Context) {
	var req dto.EventCreate
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request", "detail": err.Error()})
		return
	}

	event := model.Event{
		ID:         uuid.New(),
		EventType:  req.EventType,
		Source:     req.Source,
		DetailType: req.DetailType,
		ResourceID: req.ResourceID,
		RawPayload: marshalJSON(req.RawPayload),
		Status:     model.StatusPending,
		TraceID:    uuid.New(),
		MaxRetries: req.MaxRetries,
	}
	if event.MaxRetries <= 0 {
		event.MaxRetries = 5
	}

	if err := h.EventRepo.Create(c.Request.Context(), &event); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "create event failed", "detail": err.Error()})
		return
	}

	// Write received log
	logEntry := model.EventLog{
		EventID:   event.ID,
		Action:    "received",
		Detail:    marshalJSON(map[string]interface{}{"source": event.Source}),
		CreatedAt: time.Now(),
	}
	_ = h.LogRepo.Create(c.Request.Context(), &logEntry)

	// Dispatch for async processing
	if err := h.Dispatcher.Dispatch(c.Request.Context(), event.ID.String()); err != nil {
		// Non-fatal: event is persisted, dispatch can be retried
		_ = err
	}

	c.JSON(http.StatusCreated, toEventOut(&event))
}

// BatchCreateEvents handles POST /api/v1/events/batch
func (h *EventsHandler) BatchCreateEvents(c *gin.Context) {
	var reqs dto.BatchCreateRequest
	if err := c.ShouldBindJSON(&reqs); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request", "detail": err.Error()})
		return
	}

	events := make([]model.Event, 0, len(reqs))
	for _, req := range reqs {
		event := model.Event{
			ID:         uuid.New(),
			EventType:  req.EventType,
			Source:     req.Source,
			DetailType: req.DetailType,
			ResourceID: req.ResourceID,
			RawPayload: marshalJSON(req.RawPayload),
			Status:     model.StatusPending,
			TraceID:    uuid.New(),
			MaxRetries: req.MaxRetries,
		}
		if event.MaxRetries <= 0 {
			event.MaxRetries = 5
		}
		events = append(events, event)
	}

	if err := h.EventRepo.BatchCreate(c.Request.Context(), events); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "batch create failed", "detail": err.Error()})
		return
	}

	// Write logs and dispatch each event
	for i := range events {
		logEntry := model.EventLog{
			EventID:   events[i].ID,
			Action:    "received",
			Detail:    marshalJSON(map[string]interface{}{"source": events[i].Source, "batch": true}),
			CreatedAt: time.Now(),
		}
		_ = h.LogRepo.Create(c.Request.Context(), &logEntry)

		_ = h.Dispatcher.Dispatch(c.Request.Context(), events[i].ID.String())
	}

	c.JSON(http.StatusCreated, gin.H{
		"count": len(events),
		"items": toEventOutList(events),
	})
}

// ListEvents handles GET /api/v1/events
func (h *EventsHandler) ListEvents(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "20"))
	status := c.Query("status")
	eventType := c.Query("event_type")
	source := c.Query("source")
	search := c.Query("search")
	searchField := c.Query("search_field")

	params := repository.ListParams{
		Page:        page,
		PageSize:    pageSize,
		Status:      status,
		EventType:   eventType,
		Source:      source,
		Search:      search,
		SearchField: searchField,
	}

	events, total, err := h.EventRepo.List(c.Request.Context(), params)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "list events failed", "detail": err.Error()})
		return
	}

	c.JSON(http.StatusOK, dto.EventListOut{
		Items:    toEventOutList(events),
		Total:    total,
		Page:     page,
		PageSize: pageSize,
	})
}

// GetEvent handles GET /api/v1/events/:event_id
func (h *EventsHandler) GetEvent(c *gin.Context) {
	id, err := uuid.Parse(c.Param("event_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	event, err := h.EventRepo.GetByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "event not found"})
		return
	}

	c.JSON(http.StatusOK, toEventOut(event))
}

// GetEventLogs handles GET /api/v1/events/:event_id/logs
func (h *EventsHandler) GetEventLogs(c *gin.Context) {
	id, err := uuid.Parse(c.Param("event_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	logs, err := h.LogRepo.ListByEventID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "list logs failed", "detail": err.Error()})
		return
	}

	out := make([]dto.EventLogOut, 0, len(logs))
	for _, l := range logs {
		var detail map[string]interface{}
		_ = json.Unmarshal(l.Detail, &detail)
		out = append(out, dto.EventLogOut{
			ID:        l.ID,
			Action:    l.Action,
			Detail:    detail,
			CreatedAt: l.CreatedAt,
		})
	}

	c.JSON(http.StatusOK, out)
}

// RetryEvent handles POST /api/v1/events/:event_id/retry
func (h *EventsHandler) RetryEvent(c *gin.Context) {
	id, err := uuid.Parse(c.Param("event_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
		return
	}

	var req dto.RetryRequest
	_ = c.ShouldBindJSON(&req) // optional body

	ctx := c.Request.Context()
	event, err := h.EventRepo.GetByID(ctx, id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "event not found"})
		return
	}

	// Only retry failed or DLQ events (force allows DLQ replay)
	if event.Status != model.StatusFailed && event.Status != model.StatusDLQ && !req.Force {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("cannot retry event in status %s", event.Status)})
		return
	}

	// Reset event for re-processing
	err = h.EventRepo.UpdateFields(ctx, id, map[string]interface{}{
		"status":       model.StatusPending,
		"retry_count":  0,
		"error_message": "",
		"processed_at": nil,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "reset event failed", "detail": err.Error()})
		return
	}

	// Write RETRY log
	logEntry := model.EventLog{
		EventID: id,
		Action:  "retry_manual",
		Detail: marshalJSON(map[string]interface{}{
			"previous_status": event.Status,
			"forced":          req.Force,
		}),
		CreatedAt: time.Now(),
	}
	_ = h.LogRepo.Create(ctx, &logEntry)

	// Dispatch
	_ = h.Dispatcher.Dispatch(ctx, id.String())

	// Return updated event
	updated, _ := h.EventRepo.GetByID(ctx, id)
	c.JSON(http.StatusOK, toEventOut(updated))
}

// ReplayDLQ handles POST /api/v1/events/dlq/replay
func (h *EventsHandler) ReplayDLQ(c *gin.Context) {
	var req dto.DlqReplayRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request", "detail": err.Error()})
		return
	}

	ctx := c.Request.Context()
	affected, err := h.EventRepo.ReplayDLQ(ctx, req.EventIDs)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "replay DLQ failed", "detail": err.Error()})
		return
	}

	// Dispatch each replayed event
	for _, id := range req.EventIDs {
		_ = h.Dispatcher.Dispatch(ctx, id.String())
	}

	c.JSON(http.StatusOK, gin.H{
		"message":     fmt.Sprintf("%d events replayed from DLQ", affected),
		"replayed":    affected,
		"requested":   len(req.EventIDs),
	})
}

// ── Helpers ─────────────────────────────────────────────────────

func marshalJSON(v interface{}) datatypes.JSON {
	b, _ := json.Marshal(v)
	return b
}

func toEventOut(e *model.Event) dto.EventOut {
	var payload map[string]interface{}
	_ = json.Unmarshal(e.RawPayload, &payload)

	return dto.EventOut{
		ID:           e.ID,
		EventType:    e.EventType,
		Source:       e.Source,
		DetailType:   e.DetailType,
		ResourceID:   e.ResourceID,
		RawPayload:   payload,
		Status:       e.Status,
		TraceID:      e.TraceID,
		RetryCount:   e.RetryCount,
		MaxRetries:   e.MaxRetries,
		Handler:      e.Handler,
		WorkerID:     e.WorkerID,
		ErrorMessage: e.ErrorMessage,
		ReceivedAt:   e.ReceivedAt,
		ProcessedAt:  e.ProcessedAt,
	}
}

func toEventOutList(events []model.Event) []dto.EventOut {
	out := make([]dto.EventOut, 0, len(events))
	for i := range events {
		out = append(out, toEventOut(&events[i]))
	}
	return out
}
