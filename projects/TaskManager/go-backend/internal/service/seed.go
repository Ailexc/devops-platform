package service

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"cmdb-go/internal/model"

	"gorm.io/gorm"
)

// SeedService manages demo data seeding.
type SeedService struct {
	db *gorm.DB
}

// NewSeedService creates a new seed service.
func NewSeedService(db *gorm.DB) *SeedService {
	return &SeedService{db: db}
}

// SeedDemoData creates demo data for all tables.
func (s *SeedService) SeedDemoData(ctx context.Context, reset bool) error {
	if reset {
		slog.Info("seeding: resetting all data")
		s.db.WithContext(ctx).Exec("TRUNCATE TABLE execution_records, daily_task_stats, account_regions, periodic_tasks CASCADE")
	}

	// Seed account regions
	if err := s.seedAccountRegions(ctx); err != nil {
		return fmt.Errorf("failed to seed account regions: %w", err)
	}

	// Seed periodic tasks
	if err := s.seedPeriodicTasks(ctx); err != nil {
		return fmt.Errorf("failed to seed periodic tasks: %w", err)
	}

	// Seed demo execution records
	if err := s.seedExecutionRecords(ctx); err != nil {
		return fmt.Errorf("failed to seed execution records: %w", err)
	}

	// Seed daily task stats
	if err := s.seedDailyTaskStats(ctx); err != nil {
		return fmt.Errorf("failed to seed daily task stats: %w", err)
	}

	slog.Info("seeding: completed")
	return nil
}

func (s *SeedService) seedAccountRegions(ctx context.Context) error {
	var count int64
	s.db.WithContext(ctx).Model(&model.AccountRegion{}).Count(&count)
	if count > 0 {
		slog.Info("seeding: account_regions already populated, skipping")
		return nil
	}

	regions := []model.AccountRegion{
		{Account: "生产环境", AccountID: "123456789012", Region: "ap-northeast-1", Endpoint: "https://ec2.ap-northeast-1.amazonaws.com", Cron: "0 2 * * *", Concurrency: 50, Source: "seed", Enabled: true},
		{Account: "生产环境", AccountID: "123456789012", Region: "us-east-1", Endpoint: "https://ec2.us-east-1.amazonaws.com", Cron: "0 3 * * *", Concurrency: 50, Source: "seed", Enabled: true},
		{Account: "测试环境", AccountID: "987654321098", Region: "ap-northeast-1", Endpoint: "https://ec2.ap-northeast-1.amazonaws.com", Cron: "0 4 * * *", Concurrency: 20, Source: "seed", Enabled: true},
	}

	slog.Info("seeding: account_regions", "count", len(regions))
	return s.db.WithContext(ctx).Create(&regions).Error
}

func (s *SeedService) seedPeriodicTasks(ctx context.Context) error {
	var count int64
	s.db.WithContext(ctx).Model(&model.PeriodicTask{}).Count(&count)
	if count > 0 {
		slog.Info("seeding: periodic_tasks already populated, skipping")
		return nil
	}

	// Sentinel cron (Feb 31) for disabled tasks
	sentinelCron := "0 0 31 2 *"

	tasks := []model.PeriodicTask{
		{Name: "生产环境-ap-northeast-1-_region-dispatch", Task: "orchestrator:dispatch", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-计算-EC2", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-计算-SecurityGroup", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-计算-NetworkInterface", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-网络-VPC", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-网络-Subnet", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-ap-northeast-1-存储-RDS", Task: "worker:resource_sync", Enabled: false, Crontab: sentinelCron},
		{Name: "生产环境-us-east-1-_region-dispatch", Task: "orchestrator:dispatch", Enabled: false, Crontab: sentinelCron},
		{Name: "测试环境-ap-northeast-1-_region-dispatch", Task: "orchestrator:dispatch", Enabled: false, Crontab: sentinelCron},
	}

	slog.Info("seeding: periodic_tasks", "count", len(tasks))
	return s.db.WithContext(ctx).Create(&tasks).Error
}

func (s *SeedService) seedExecutionRecords(ctx context.Context) error {
	var count int64
	s.db.WithContext(ctx).Model(&model.ExecutionRecord{}).Count(&count)
	if count > 0 {
		slog.Info("seeding: execution_records already populated, skipping")
		return nil
	}

	// Create some demo execution records
	records := []model.ExecutionRecord{
		{
			Scope: "region", TaskName: "生产环境/ap-northeast-1 区域同步", Module: "AWS", Target: "生产环境 / ap-northeast-1",
			Trigger: "人工", Status: "success", Duration: "12.3s",
			Params: &model.JSONMap{"account": "生产环境", "region": "ap-northeast-1", "scope": "region", "target": "", "mode": "full", "trigger": "人工"},
		},
		{
			Scope: "region", TaskName: "生产环境/us-east-1 区域同步", Module: "AWS", Target: "生产环境 / us-east-1",
			Trigger: "Cron", Status: "success", Duration: "8.7s",
			Params: &model.JSONMap{"account": "生产环境", "region": "us-east-1", "scope": "region", "target": "", "mode": "full", "trigger": "Cron"},
		},
		{
			Scope: "resource", TaskName: "测试环境/ap-northeast-1 EC2同步", Module: "AWS", Target: "测试环境 / ap-northeast-1",
			Trigger: "人工", Status: "failed", Error: "AWS API 限流", Duration: "3.1s",
			Params: &model.JSONMap{"account": "测试环境", "region": "ap-northeast-1", "scope": "resource", "target": "EC2", "mode": "full", "trigger": "人工"},
		},
	}

	slog.Info("seeding: execution_records", "count", len(records))
	return s.db.WithContext(ctx).Create(&records).Error
}

func (s *SeedService) seedDailyTaskStats(ctx context.Context) error {
	var count int64
	s.db.WithContext(ctx).Model(&model.DailyTaskStat{}).Count(&count)
	if count > 0 {
		slog.Info("seeding: daily_task_stats already populated, skipping")
		return nil
	}

	// Create 7 days of demo stats
	var stats []model.DailyTaskStat
	for i := 6; i >= 0; i-- {
		d := time.Now().AddDate(0, 0, -i)
		stats = append(stats, model.DailyTaskStat{
			StatDate:    d.Truncate(24 * time.Hour),
			Module:      "AWS",
			Total:       3 + i%3,
			Success:     2 + i%3,
			Failed:      1,
			TotalDuration: float64(20+i*5) * 1.0,
			SyncedCount:   50 + i*10,
		})
	}

	slog.Info("seeding: daily_task_stats", "count", len(stats))
	return s.db.WithContext(ctx).Create(&stats).Error
}
