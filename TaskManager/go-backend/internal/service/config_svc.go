package service

import (
	"context"
	"fmt"

	"cmdb-go/internal/model"

	"gorm.io/gorm"
)

// ConfigService manages account/region configuration.
type ConfigService struct {
	db *gorm.DB
}

// NewConfigService creates a new config service.
func NewConfigService(db *gorm.DB) *ConfigService {
	return &ConfigService{db: db}
}

// AccountRegionGroup represents an account with its regions.
type AccountRegionGroup struct {
	Name      string           `json:"name"`
	AccountID string           `json:"account_id"`
	Regions   []RegionInfo     `json:"regions"`
}

// RegionInfo holds region details.
type RegionInfo struct {
	Code        string `json:"code"`
	Endpoint    string `json:"endpoint"`
	Cron        string `json:"cron"`
	Concurrency int    `json:"concurrency"`
	Enabled     bool   `json:"enabled"`
	Source      string `json:"source"`
}

// ListAccountRegions returns all account regions grouped by account.
func (s *ConfigService) ListAccountRegions(ctx context.Context) ([]AccountRegionGroup, error) {
	var regions []model.AccountRegion
	if err := s.db.WithContext(ctx).Order("account, region").Find(&regions).Error; err != nil {
		return nil, err
	}

	groupMap := make(map[string]*AccountRegionGroup)
	var order []string

	for _, r := range regions {
		if _, ok := groupMap[r.Account]; !ok {
			groupMap[r.Account] = &AccountRegionGroup{
				Name:      r.Account,
				AccountID: r.AccountID,
			}
			order = append(order, r.Account)
		}
		groupMap[r.Account].Regions = append(groupMap[r.Account].Regions, RegionInfo{
			Code:        r.Region,
			Endpoint:    r.Endpoint,
			Cron:        r.Cron,
			Concurrency: r.Concurrency,
			Enabled:     r.Enabled,
			Source:      r.Source,
		})
	}

	var result []AccountRegionGroup
	for _, name := range order {
		result = append(result, *groupMap[name])
	}
	return result, nil
}

// GetAccountRegion retrieves a single account region.
func (s *ConfigService) GetAccountRegion(ctx context.Context, account, region string) (*model.AccountRegion, error) {
	var ar model.AccountRegion
	if err := s.db.WithContext(ctx).Where("account = ? AND region = ?", account, region).First(&ar).Error; err != nil {
		return nil, err
	}
	return &ar, nil
}

// UpdateRegionConfig updates a region's configuration.
func (s *ConfigService) UpdateRegionConfig(ctx context.Context, account, region string, cron *string, concurrency *int) error {
	ar, err := s.GetAccountRegion(ctx, account, region)
	if err != nil {
		return fmt.Errorf("账号/区域未配置: %s/%s", account, region)
	}

	updates := map[string]interface{}{}
	if cron != nil {
		updates["cron"] = *cron
	}
	if concurrency != nil {
		updates["concurrency"] = *concurrency
	}

	if len(updates) > 0 {
		return s.db.WithContext(ctx).Model(ar).Updates(updates).Error
	}
	return nil
}

// ListAccounts returns a simple account list.
func (s *ConfigService) ListAccounts(ctx context.Context) ([]map[string]interface{}, error) {
	groups, err := s.ListAccountRegions(ctx)
	if err != nil {
		return nil, err
	}

	var result []map[string]interface{}
	for _, g := range groups {
		result = append(result, map[string]interface{}{
			"name":         g.Name,
			"account_id":   g.AccountID,
			"region_count": len(g.Regions),
		})
	}
	return result, nil
}

// SeedDefaultData creates default account/region entries if none exist.
func (s *ConfigService) SeedDefaultData(ctx context.Context) error {
	var count int64
	s.db.WithContext(ctx).Model(&model.AccountRegion{}).Count(&count)
	if count > 0 {
		return nil
	}

	defaults := []model.AccountRegion{
		{Account: "生产环境", AccountID: "123456789012", Region: "ap-northeast-1", Endpoint: "https://ec2.ap-northeast-1.amazonaws.com", Cron: "0 2 * * *", Concurrency: 50, Source: "seed", Enabled: true},
		{Account: "生产环境", AccountID: "123456789012", Region: "us-east-1", Endpoint: "https://ec2.us-east-1.amazonaws.com", Cron: "0 3 * * *", Concurrency: 50, Source: "seed", Enabled: true},
		{Account: "测试环境", AccountID: "987654321098", Region: "ap-northeast-1", Endpoint: "https://ec2.ap-northeast-1.amazonaws.com", Cron: "0 4 * * *", Concurrency: 20, Source: "seed", Enabled: true},
	}

	return s.db.WithContext(ctx).Create(&defaults).Error
}
