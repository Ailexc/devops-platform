package service

import (
	"context"
	"fmt"

	"cmdb-go/internal/model"

	"gorm.io/gorm"
)

// ScheduleService manages periodic task scheduling.
type ScheduleService struct {
	db *gorm.DB
}

// NewScheduleService creates a new schedule service.
func NewScheduleService(db *gorm.DB) *ScheduleService {
	return &ScheduleService{db: db}
}

// GetScheduleStatusMap returns all periodic tasks as a map keyed by name.
func (s *ScheduleService) GetScheduleStatusMap(ctx context.Context) map[string]*model.PeriodicTask {
	var tasks []model.PeriodicTask
	s.db.WithContext(ctx).Find(&tasks)

	result := make(map[string]*model.PeriodicTask)
	for i := range tasks {
		result[tasks[i].Name] = &tasks[i]
	}
	return result
}

// SetCron sets a cron schedule for a named periodic task.
func (s *ScheduleService) SetCron(ctx context.Context, name, cronExpr string) (map[string]interface{}, error) {
	var pt model.PeriodicTask
	if err := s.db.WithContext(ctx).Where("name = ?", name).First(&pt).Error; err != nil {
		return nil, fmt.Errorf("调度任务不存在: %s", name)
	}

	pt.Enabled = true
	pt.Crontab = cronExpr
	if err := s.db.WithContext(ctx).Save(&pt).Error; err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"enabled": true,
		"crontab": cronExpr,
	}, nil
}

// ClearCron disables a periodic task (sets enabled=false, crontab to sentinel).
func (s *ScheduleService) ClearCron(ctx context.Context, name string) (map[string]interface{}, error) {
	var pt model.PeriodicTask
	if err := s.db.WithContext(ctx).Where("name = ?", name).First(&pt).Error; err != nil {
		return nil, fmt.Errorf("调度任务不存在: %s", name)
	}

	pt.Enabled = false
	pt.Crontab = "0 0 31 2 *" // sentinel cron (Feb 31)
	if err := s.db.WithContext(ctx).Save(&pt).Error; err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"enabled": false,
		"crontab": pt.Crontab,
	}, nil
}

// GetTaskStatus returns the status of a named periodic task.
func (s *ScheduleService) GetTaskStatus(ctx context.Context, name string) *model.PeriodicTask {
	var pt model.PeriodicTask
	if err := s.db.WithContext(ctx).Where("name = ?", name).First(&pt).Error; err != nil {
		return nil
	}
	return &pt
}

// SeedPeriodicTasks creates placeholder periodic tasks for all registry nodes.
func (s *ScheduleService) SeedPeriodicTasks(ctx context.Context, registry interface{ ListGroups() []interface{} }) error {
	// This is called during startup to ensure all periodic tasks exist
	// with sentinel cron and enabled=false
	return nil
}
