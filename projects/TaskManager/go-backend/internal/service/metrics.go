package service

import (
	"context"
	"fmt"
	"time"

	"cmdb-go/internal/model"
	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/cmdbstore"

	"gorm.io/gorm"
)

// MetricsService provides dashboard metrics and statistics.
type MetricsService struct {
	db       *gorm.DB
	store    *cmdbstore.Store
	registry *orchestrator.Registry
}

// NewMetricsService creates a new metrics service.
func NewMetricsService(db *gorm.DB, store *cmdbstore.Store, registry *orchestrator.Registry) *MetricsService {
	return &MetricsService{db: db, store: store, registry: registry}
}

// DashboardStats holds the dashboard summary statistics.
type DashboardStats struct {
	TodayTasks        int64   `json:"today_tasks"`
	SuccessRate24h    string  `json:"success_rate_24h"`
	SuccessRate7d     string  `json:"success_rate_7d"`
	WeeklyTotal       int64   `json:"weekly_total"`
	MonthlyTotal      int64   `json:"monthly_total"`
	CumulativeSynced  int64   `json:"cumulative_synced"`
	RunningNow        int     `json:"running_now"`
	PendingErrors     int64   `json:"pending_errors"`
	TotalCMDBResources int64 `json:"total_cmdb_resources"`
}

// GetDashboardStats returns the dashboard summary.
func (s *MetricsService) GetDashboardStats(ctx context.Context) (*DashboardStats, error) {
	today := time.Now().Truncate(24 * time.Hour)
	weekAgo := today.AddDate(0, 0, -6)
	monthAgo := today.AddDate(0, 0, -29)

	stats := &DashboardStats{}

	// Today
	var todayStat struct {
		Total   int64
		Success int64
		Failed  int64
		Synced  int64
	}
	s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).
		Where("stat_date >= ?", today).
		Select("COALESCE(SUM(total),0) as total, COALESCE(SUM(success),0) as success, COALESCE(SUM(failed),0) as failed, COALESCE(SUM(synced_count),0) as synced").
		Scan(&todayStat)
	stats.TodayTasks = todayStat.Total
	stats.PendingErrors = todayStat.Failed
	if todayStat.Total > 0 {
		stats.SuccessRate24h = fmt.Sprintf("%.1f%%", float64(todayStat.Success)/float64(todayStat.Total)*100)
	} else {
		stats.SuccessRate24h = "—"
	}

	// 7 days
	var weekStat struct {
		Total   int64
		Success int64
		Synced  int64
	}
	s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).
		Where("stat_date >= ?", weekAgo).
		Select("COALESCE(SUM(total),0) as total, COALESCE(SUM(success),0) as success, COALESCE(SUM(synced_count),0) as synced").
		Scan(&weekStat)
	stats.WeeklyTotal = weekStat.Total
	if weekStat.Total > 0 {
		stats.SuccessRate7d = fmt.Sprintf("%.1f%%", float64(weekStat.Success)/float64(weekStat.Total)*100)
	} else {
		stats.SuccessRate7d = "—"
	}

	// 30 days
	var monthStat struct {
		Total  int64
		Synced int64
	}
	s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).
		Where("stat_date >= ?", monthAgo).
		Select("COALESCE(SUM(total),0) as total, COALESCE(SUM(synced_count),0) as synced").
		Scan(&monthStat)
	stats.MonthlyTotal = monthStat.Total
	stats.CumulativeSynced = monthStat.Synced

	// Running now
	var runningCount int64
	s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).
		Where("status = ? AND parent_id IS NULL", "running").
		Count(&runningCount)
	stats.RunningNow = int(runningCount)

	// Total CMDB resources
	total, _ := s.store.TotalCount(ctx)
	stats.TotalCMDBResources = total

	return stats, nil
}

// WorkerStatus holds worker pool status.
type WorkerStatus struct {
	Workers    []WorkerInfo `json:"workers"`
	TotalTasks int          `json:"total_tasks"`
}

// WorkerInfo holds info about a single worker.
type WorkerInfo struct {
	Name       string `json:"name"`
	Status     string `json:"status"`
	Active     int    `json:"active"`
	Processed  int    `json:"processed"`
}

// GetWorkerStatus returns worker pool status.
func (s *MetricsService) GetWorkerStatus(ctx context.Context) *WorkerStatus {
	// In Go + asynq, worker status comes from asynq Inspector
	// For demo, return placeholder
	return &WorkerStatus{
		Workers: []WorkerInfo{
			{Name: "go-worker-1", Status: "active", Active: 0, Processed: 0},
		},
		TotalTasks: 1,
	}
}

// ResourceHealth holds module health info.
type ResourceHealth struct {
	Modules   []ModuleHealth          `json:"modules"`
	Freshness map[string]string       `json:"freshness"`
}

// ModuleHealth holds health info for a single module.
type ModuleHealth struct {
	Name   string `json:"name"`
	Rate   string `json:"rate"`
	Failed int64  `json:"failed"`
	Total  int64  `json:"total"`
	Synced int64  `json:"synced"`
}

// GetResourceHealth returns module health stats.
func (s *MetricsService) GetResourceHealth(ctx context.Context) (*ResourceHealth, error) {
	monthAgo := time.Now().AddDate(0, 0, -29)

	var rows []struct {
		Module string
		Total  int64
		Failed int64
		Synced int64
	}
	s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).
		Where("stat_date >= ?", monthAgo).
		Select("module, COALESCE(SUM(total),0) as total, COALESCE(SUM(failed),0) as failed, COALESCE(SUM(synced_count),0) as synced").
		Group("module").
		Scan(&rows)

	modules := make([]ModuleHealth, 0)
	for _, row := range rows {
		rate := "—"
		if row.Total > 0 {
			rate = fmt.Sprintf("%.1f%%", float64(row.Total-row.Failed)/float64(row.Total)*100)
		}
		modules = append(modules, ModuleHealth{
			Name:   row.Module,
			Rate:   rate,
			Failed: row.Failed,
			Total:  row.Total,
			Synced: row.Synced,
		})
	}

	return &ResourceHealth{
		Modules:   modules,
		Freshness: make(map[string]string),
	}, nil
}

// TaskTrend holds daily task trend data.
type TaskTrend struct {
	Date    string `json:"date"`
	Total   int64  `json:"total"`
	Success int64  `json:"success"`
	Failed  int64  `json:"failed"`
}

// GetTaskTrend returns 7-day task trend.
func (s *MetricsService) GetTaskTrend(ctx context.Context) ([]TaskTrend, error) {
	trend := make([]TaskTrend, 0)
	for i := 6; i >= 0; i-- {
		d := time.Now().AddDate(0, 0, -i)
		dateStr := d.Format("01-02")

		var stat struct {
			Total   int64
			Success int64
			Failed  int64
		}
		s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).
			Where("stat_date = ?", d.Truncate(24*time.Hour)).
			Select("COALESCE(SUM(total),0) as total, COALESCE(SUM(success),0) as success, COALESCE(SUM(failed),0) as failed").
			Scan(&stat)

		trend = append(trend, TaskTrend{
			Date:    dateStr,
			Total:   stat.Total,
			Success: stat.Success,
			Failed:  stat.Failed,
		})
	}
	return trend, nil
}

// HealthRanking holds health ranking data.
type HealthRanking struct {
	TopFailedModules []FailedModule      `json:"top_failed_modules"`
	TopDuration      []DurationEntry     `json:"top_duration"`
}

// FailedModule holds failed module stats.
type FailedModule struct {
	Module string `json:"module"`
	Count  int64  `json:"count"`
}

// DurationEntry holds duration ranking entry.
type DurationEntry struct {
	Task     string `json:"task"`
	Target   string `json:"target"`
	Duration string `json:"duration"`
}

// GetHealthRanking returns health ranking data.
func (s *MetricsService) GetHealthRanking(ctx context.Context) (*HealthRanking, error) {
	cutoff := time.Now().AddDate(0, 0, -3)

	var failedRows []FailedModule
	s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).
		Where("parent_id IS NULL AND started_at >= ? AND status IN (?)", cutoff, []string{"failed", "partial"}).
		Select("module, COUNT(*) as count").
		Group("module").
		Order("count DESC").
		Limit(5).
		Scan(&failedRows)

	var topDuration []DurationEntry
	s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).
		Where("parent_id IS NULL AND started_at >= ? AND status = ?", cutoff, "success").
		Order("(finished_at - started_at) DESC").
		Limit(5).
		Select("task_name as task, target, duration").
		Scan(&topDuration)

	return &HealthRanking{
		TopFailedModules: failedRows,
		TopDuration:      topDuration,
	}, nil
}

// CurrentRunning holds currently running tasks.
type CurrentRunning struct {
	Running []RunningTask `json:"running"`
	Locks   []interface{} `json:"locks"`
}

// RunningTask holds info about a running task.
type RunningTask struct {
	ID      string `json:"id"`
	Task    string `json:"task"`
	Target  string `json:"target"`
	Scope   string `json:"scope"`
	Trigger string `json:"trigger"`
	Start   string `json:"start"`
}

// GetCurrentRunning returns currently running tasks.
func (s *MetricsService) GetCurrentRunning(ctx context.Context) (*CurrentRunning, error) {
	var records []model.ExecutionRecord
	s.db.WithContext(ctx).
		Where("status = ? AND parent_id IS NULL", "running").
		Order("started_at DESC").
		Limit(10).
		Find(&records)

	// Ensure non-nil slices (JSON → [] instead of null)
	running := make([]RunningTask, 0)
	for _, r := range records {
		r.FormatID()
		start := "-"
		if !r.StartedAt.IsZero() {
			start = r.StartedAt.Format("15:04:05")
		}
		running = append(running, RunningTask{
			ID:      r.RecordID,
			Task:    r.TaskName,
			Target:  r.Target,
			Scope:   r.Scope,
			Trigger: r.Trigger,
			Start:   start,
		})
	}

	return &CurrentRunning{Running: running, Locks: make([]interface{}, 0)}, nil
}

// RecentEvent holds a recent event entry.
type RecentEvent struct {
	ID      string `json:"id"`
	Task    string `json:"task"`
	Status  string `json:"status"`
	Type    string `json:"type"`
	Time    string `json:"time"`
	Target  string `json:"target"`
}

// GetRecentEvents returns recent events.
func (s *MetricsService) GetRecentEvents(ctx context.Context) ([]RecentEvent, error) {
	var records []model.ExecutionRecord
	s.db.WithContext(ctx).
		Where("parent_id IS NULL AND status != ?", "running").
		Order("started_at DESC").
		Limit(20).
		Find(&records)

	events := make([]RecentEvent, 0)
	for _, r := range records {
		r.FormatID()
		eventType := "success"
		if r.Status == "failed" || r.Status == "partial" {
			eventType = "error"
		} else if r.Status == "running" {
			eventType = "warning"
		}
		events = append(events, RecentEvent{
			ID:     r.RecordID,
			Task:   r.TaskName,
			Status: r.Status,
			Type:   eventType,
			Time:   r.StartedAt.Format("01-02 15:04"),
			Target: r.Target,
		})
	}
	return events, nil
}

// ResourceBreakdown holds resource breakdown data.
type ResourceBreakdown struct {
	Breakdown []BreakdownEntry `json:"breakdown"`
}

// BreakdownEntry holds a single resource type count.
type BreakdownEntry struct {
	Name  string `json:"name"`
	Count int64  `json:"count"`
}

// GetResourceBreakdown returns resource type counts from CMDB store.
func (s *MetricsService) GetResourceBreakdown(ctx context.Context) (*ResourceBreakdown, error) {
	entries := make([]BreakdownEntry, 0)
	for _, g := range s.registry.ListGroups() {
		for _, res := range g.Resources {
			count, _ := s.store.CountByModule(ctx, res.Name)
			entries = append(entries, BreakdownEntry{
				Name:  res.Name,
				Count: count,
			})
		}
	}
	return &ResourceBreakdown{Breakdown: entries}, nil
}

// AWSResourceNode represents a node in the AWS resource tree.
type AWSResourceNode struct {
	Name     string             `json:"name"`
	Type     string             `json:"type,omitempty"`
	Children []AWSResourceNode  `json:"children,omitempty"`
}

// GetAWSResourceTree returns the AWS resource tree.
func (s *MetricsService) GetAWSResourceTree(ctx context.Context) ([]AWSResourceNode, error) {
	tree := make([]AWSResourceNode, 0)
	for _, g := range s.registry.ListGroups() {
		node := AWSResourceNode{
			Name: g.Name,
			Type: "group",
			Children: make([]AWSResourceNode, 0),
		}
		for _, res := range g.Resources {
			count, _ := s.store.CountByModule(ctx, res.Name)
			node.Children = append(node.Children, AWSResourceNode{
				Name: fmt.Sprintf("%s (%d)", res.Name, count),
				Type: "resource",
			})
		}
		tree = append(tree, node)
	}
	return tree, nil
}
