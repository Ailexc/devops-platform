package history

import (
	"net/http"
	"strconv"

	"cmdb-go/internal/service"

	"github.com/gin-gonic/gin"
)

// Handler holds history API handlers.
type Handler struct {
	executionSvc *service.ExecutionService
}

// NewHandler creates a new history handler.
func NewHandler(executionSvc *service.ExecutionService) *Handler {
	return &Handler{executionSvc: executionSvc}
}

// RegisterRoutes registers all history routes.
func (h *Handler) RegisterRoutes(rg *gin.RouterGroup) {
	hist := rg.Group("/history")
	{
		hist.GET("/", h.List)
		hist.GET("/:record_id/", h.Detail)
		hist.POST("/:record_id/retry/", h.Retry)
	}
}

// List returns paginated execution history.
func (h *Handler) List(c *gin.Context) {
	ctx := c.Request.Context()

	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "50"))
	module := c.Query("module")
	status := c.Query("status")
	scope := c.Query("scope")
	trigger := c.Query("trigger")

	records, total, err := h.executionSvc.ListRecords(ctx, page, pageSize, module, status, scope, trigger)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"records":   records,
		"total":     total,
		"page":      page,
		"page_size": pageSize,
	})
}

// Detail returns a single execution record with children.
func (h *Handler) Detail(c *gin.Context) {
	ctx := c.Request.Context()
	id, err := strconv.ParseInt(c.Param("record_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid record_id"})
		return
	}

	record, children, err := h.executionSvc.GetRecordDetail(ctx, id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "记录不存在"})
		return
	}

	result := gin.H{
		"id":            record.RecordID,
		"task":          record.TaskName,
		"module":        record.Module,
		"target":        record.Target,
		"trigger":       record.Trigger,
		"scope":         record.Scope,
		"scope_label":   record.ScopeLabel,
		"status":        record.Status,
		"celery_task_id": record.CeleryTaskID,
		"error":         record.Error,
		"detail":        record.Detail,
		"duration":      record.Duration,
		"result":        record.Result,
		"lifecycle_events": record.LifecycleEvents,
		"params":        record.Params,
		"started_at":    record.StartedAt,
		"finished_at":   record.FinishedAt,
		"children":      children,
	}

	c.JSON(http.StatusOK, result)
}

// Retry retries a failed execution record.
func (h *Handler) Retry(c *gin.Context) {
	ctx := c.Request.Context()
	id, err := strconv.ParseInt(c.Param("record_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid record_id"})
		return
	}

	// Get the original record
	record, err := h.executionSvc.GetRecord(ctx, id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "记录不存在"})
		return
	}

	// Extract dispatch params from the record
	if record.Params == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "该记录没有派发参数，无法重试"})
		return
	}

	params := (*record.Params)
	account, _ := params["account"].(string)
	region, _ := params["region"].(string)
	if account == "" || region == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "该记录没有派发参数，无法重试"})
		return
	}

	mode, _ := params["mode"].(string)
	if mode == "" {
		mode = "full"
	}
	target, _ := params["target"].(string)
	resourceIDs, _ := params["resource_ids"].([]interface{})
	var rids []string
	for _, r := range resourceIDs {
		if s, ok := r.(string); ok {
			rids = append(rids, s)
		}
	}

	dispatchParams := service.DispatchParams{
		Account:     account,
		Region:      region,
		Scope:       record.Scope,
		Target:      target,
		Mode:        mode,
		Trigger:     "人工",
		ResourceIDs: rids,
	}

	outcome, err := h.executionSvc.DispatchExecution(ctx, dispatchParams)
	if err != nil {
		if tcErr, ok := err.(*service.TaskConflictError); ok {
			c.JSON(http.StatusConflict, gin.H{"error": tcErr.Error(), "conflict": tcErr.Conflict})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"execution_id": outcome.Record.ID,
		"status":       "dispatched",
	})
}
