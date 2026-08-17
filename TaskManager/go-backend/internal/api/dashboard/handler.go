package dashboard

import (
	"net/http"

	"cmdb-go/internal/service"

	"github.com/gin-gonic/gin"
)

// Handler holds dashboard API handlers.
type Handler struct {
	metricsSvc *service.MetricsService
}

// NewHandler creates a new dashboard handler.
func NewHandler(metricsSvc *service.MetricsService) *Handler {
	return &Handler{metricsSvc: metricsSvc}
}

// RegisterRoutes registers all dashboard routes.
func (h *Handler) RegisterRoutes(rg *gin.RouterGroup) {
	dash := rg.Group("/dashboard")
	{
		dash.GET("/stats/", h.Stats)
		dash.GET("/workers/", h.Workers)
		dash.GET("/resource-health/", h.ResourceHealth)
		dash.GET("/task-trend/", h.TaskTrend)
		dash.GET("/health-ranking/", h.HealthRanking)
		dash.GET("/current/", h.Current)
		dash.GET("/recent-events/", h.RecentEvents)
		dash.GET("/resource-breakdown/", h.ResourceBreakdown)
		dash.GET("/aws-resources/", h.AWSResources)
	}
}

// Stats returns dashboard summary statistics.
func (h *Handler) Stats(c *gin.Context) {
	ctx := c.Request.Context()
	stats, err := h.metricsSvc.GetDashboardStats(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, stats)
}

// Workers returns worker pool status.
func (h *Handler) Workers(c *gin.Context) {
	ctx := c.Request.Context()
	status := h.metricsSvc.GetWorkerStatus(ctx)
	c.JSON(http.StatusOK, status)
}

// ResourceHealth returns module health stats.
func (h *Handler) ResourceHealth(c *gin.Context) {
	ctx := c.Request.Context()
	health, err := h.metricsSvc.GetResourceHealth(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, health)
}

// TaskTrend returns 7-day task trend.
func (h *Handler) TaskTrend(c *gin.Context) {
	ctx := c.Request.Context()
	trend, err := h.metricsSvc.GetTaskTrend(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, trend)
}

// HealthRanking returns health ranking data.
func (h *Handler) HealthRanking(c *gin.Context) {
	ctx := c.Request.Context()
	ranking, err := h.metricsSvc.GetHealthRanking(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, ranking)
}

// Current returns currently running tasks.
func (h *Handler) Current(c *gin.Context) {
	ctx := c.Request.Context()
	current, err := h.metricsSvc.GetCurrentRunning(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, current)
}

// RecentEvents returns recent events.
func (h *Handler) RecentEvents(c *gin.Context) {
	ctx := c.Request.Context()
	events, err := h.metricsSvc.GetRecentEvents(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, events)
}

// ResourceBreakdown returns resource type counts.
func (h *Handler) ResourceBreakdown(c *gin.Context) {
	ctx := c.Request.Context()
	breakdown, err := h.metricsSvc.GetResourceBreakdown(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, breakdown.Breakdown)
}

// AWSResources returns the AWS resource tree.
func (h *Handler) AWSResources(c *gin.Context) {
	ctx := c.Request.Context()
	tree, err := h.metricsSvc.GetAWSResourceTree(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"tree": tree})
}
