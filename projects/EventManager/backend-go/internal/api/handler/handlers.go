package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"event-flow/internal/eventhandler"
	"event-flow/internal/model"
	"event-flow/internal/repository"
)

// HandlersHandler holds dependencies for handler listing endpoints.
type HandlersHandler struct {
	EventRepo *repository.EventRepo
	DB        *gorm.DB
}

// NewHandlersHandler creates a new HandlersHandler.
func NewHandlersHandler(eventRepo *repository.EventRepo, db *gorm.DB) *HandlersHandler {
	return &HandlersHandler{
		EventRepo: eventRepo,
		DB:        db,
	}
}

// ListHandlers handles GET /api/v1/handlers
func (h *HandlersHandler) ListHandlers(c *gin.Context) {
	ctx := c.Request.Context()

	// Get metadata from the event handler registry
	metadata := eventhandler.GetAllMetadata()

	// Also query EventHandlerConfig from database for additional configs
	var configs []model.EventHandlerConfig
	if err := h.DB.WithContext(ctx).Where("is_active = ?", true).Find(&configs).Error; err != nil {
		// Non-fatal: registry metadata is still useful
		_ = err
	}

	// Merge registry metadata and DB configs
	type handlerInfo struct {
		Name             string                 `json:"name"`
		EventTypePattern string                 `json:"event_type_pattern"`
		HandlerClass     string                 `json:"handler_class"`
		Timeout          int                    `json:"timeout"`
		MaxRetries       int                    `json:"max_retries"`
		IsActive         bool                   `json:"is_active"`
		Description      string                 `json:"description"`
		Category         string                 `json:"category"`
		Icon             string                 `json:"icon"`
		Events           []map[string]interface{} `json:"events,omitempty"`
		Schema           map[string]interface{} `json:"schema,omitempty"`
		Example          interface{}            `json:"example,omitempty"`
	}

	result := make([]handlerInfo, 0)

	// Add from DB configs
	for _, cfg := range configs {
		result = append(result, handlerInfo{
			Name:             cfg.Name,
			EventTypePattern: cfg.EventTypePattern,
			HandlerClass:     cfg.HandlerClass,
			Timeout:          cfg.Timeout,
			MaxRetries:       cfg.MaxRetries,
			IsActive:         cfg.IsActive,
			Description:      cfg.Description,
		})
	}

	// Add from registry metadata (if not already in DB)
	existingPatterns := make(map[string]bool)
	for _, cfg := range configs {
		existingPatterns[cfg.EventTypePattern] = true
	}

	for _, meta := range metadata {
		if !existingPatterns[meta.Pattern] {
			result = append(result, handlerInfo{
				Name:             meta.Handler,
				EventTypePattern: meta.Pattern,
				IsActive:         true,
				Description:      meta.Description,
				Category:         meta.Category,
				Icon:             meta.Icon,
				Events:           meta.Events,
				Schema:           meta.Schema,
				Example:          meta.Example,
			})
		}
	}

	c.JSON(http.StatusOK, result)
}

// ListEventTypes handles GET /api/v1/handlers/event-types
func (h *HandlersHandler) ListEventTypes(c *gin.Context) {
	ctx := c.Request.Context()

	metadata := eventhandler.GetAllMetadata()

	type eventTypeInfo struct {
		Pattern     string `json:"pattern"`
		Category    string `json:"category"`
		Icon        string `json:"icon"`
		Description string `json:"description"`
		Handler     string `json:"handler"`
	}

	result := make([]eventTypeInfo, 0, len(metadata))
	for _, meta := range metadata {
		result = append(result, eventTypeInfo{
			Pattern:     meta.Pattern,
			Category:    meta.Category,
			Icon:        meta.Icon,
			Description: meta.Description,
			Handler:     meta.Handler,
		})
	}

	_ = ctx // available if needed
	c.JSON(http.StatusOK, result)
}
