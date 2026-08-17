package handler

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/hibiken/asynq"

	"event-flow/internal/api/dto"
	"event-flow/internal/repository"
)

// StatsHandler holds dependencies for statistics endpoints.
type StatsHandler struct {
	EventRepo *repository.EventRepo
	Inspector *asynq.Inspector
}

// NewStatsHandler creates a new StatsHandler.
func NewStatsHandler(eventRepo *repository.EventRepo, inspector *asynq.Inspector) *StatsHandler {
	return &StatsHandler{
		EventRepo: eventRepo,
		Inspector: inspector,
	}
}

// GetStats handles GET /api/v1/stats
func (h *StatsHandler) GetStats(c *gin.Context) {
	ctx := c.Request.Context()
	oneHourAgo := time.Now().Add(-1 * time.Hour)

	total, err := h.EventRepo.Count(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "count failed"})
		return
	}

	byStatus, err := h.EventRepo.CountByStatus(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "count by status failed"})
		return
	}

	recentTotal, recentSuccess, avgDuration, err := h.EventRepo.GetRecentStats(ctx, oneHourAgo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "recent stats failed"})
		return
	}

	successRate := 0.0
	if recentTotal > 0 {
		successRate = float64(recentSuccess) / float64(recentTotal) * 100
	}

	queueDepth := byStatus["pending"] + byStatus["processing"]

	c.JSON(http.StatusOK, dto.StatsOut{
		Total:       total,
		ByStatus:    byStatus,
		SuccessRate: round2(successRate),
		AvgDuration: avgDuration,
		P99Duration: nil, // TODO: implement P99
		QueueDepth:  queueDepth,
	})
}

// QueueStats handles GET /api/v1/stats/queues
func (h *StatsHandler) QueueStats(c *gin.Context) {
	ctx := c.Request.Context()

	type queueItem struct {
		Name   string `json:"name"`
		Label  string `json:"label"`
		Depth  int64  `json:"depth"`
	}

	statusMap := []struct {
		Name   string
		Status string
		Label  string
	}{
		{"events", "pending", "主队列"},
		{"events.high", "processing", "高优处理中"},
		{"events.retry", "failed", "重试队列"},
		{"events.dlq", "dlq", "死信队列"},
		{"events.completed", "completed", "已完成"},
	}

	result := make([]queueItem, 0, len(statusMap))
	for _, m := range statusMap {
		count, err := h.EventRepo.ListByStatus(ctx, []string{m.Status})
		if err != nil {
			count = 0
		}
		result = append(result, queueItem{
			Name:  m.Name,
			Label: m.Label,
			Depth: count,
		})
	}

	c.JSON(http.StatusOK, result)
}

// WorkerStats handles GET /api/v1/stats/workers
func (h *StatsHandler) WorkerStats(c *gin.Context) {
	type workerInfo struct {
		ID          string `json:"id"`
		Status      string `json:"status"`
		Hostname    string `json:"hostname"`
		ActiveTasks int    `json:"active_tasks"`
		Pool        string `json:"pool"`
		Concurrency int    `json:"concurrency"`
	}

	result := dto.WorkerStatsOut{
		Workers: make([]dto.WorkerInfo, 0),
	}

	if h.Inspector == nil {
		c.JSON(http.StatusOK, result)
		return
	}

	// Get queue info from asynq
	queues, err := h.Inspector.Queues()
	if err == nil {
		for _, q := range queues {
			info, err := h.Inspector.GetQueueInfo(q)
			if err != nil {
				continue
			}
			result.QueuedTasks += int64(info.Size + info.Pending + info.Scheduled + info.Retry)
		}
	}

	c.JSON(http.StatusOK, result)
}

// ThroughputStats handles GET /api/v1/stats/throughput
func (h *StatsHandler) ThroughputStats(c *gin.Context) {
	ctx := c.Request.Context()
	since := time.Now().Add(-24 * time.Hour)

	throughput, err := h.EventRepo.GetHourlyThroughput(ctx, since)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "throughput query failed"})
		return
	}

	out := make([]dto.HourlyThroughputOut, 0, len(throughput))
	for _, t := range throughput {
		out = append(out, dto.HourlyThroughputOut{
			Hour:      t.Hour,
			Total:     t.Total,
			Completed: t.Completed,
			Failed:    t.Failed,
			Other:     t.Other,
		})
	}

	c.JSON(http.StatusOK, out)
}

// RecentFailures handles GET /api/v1/stats/recent-failures
func (h *StatsHandler) RecentFailures(c *gin.Context) {
	limit := 5
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			limit = v
		}
	}

	failures, err := h.EventRepo.GetRecentFailures(c.Request.Context(), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failures failed"})
		return
	}

	out := make([]dto.EventOut, 0, len(failures))
	for i := range failures {
		out = append(out, toEventOut(&failures[i]))
	}

	c.JSON(http.StatusOK, out)
}

func round2(f float64) float64 {
	return float64(int(f*100)) / 100
}
