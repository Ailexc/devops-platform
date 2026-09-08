package service

import (
	"context"
	"fmt"

	"cmdb-go/internal/model"
	"cmdb-go/internal/orchestrator"
	"cmdb-go/internal/pkg/lock"

	"gorm.io/gorm"
)

// TaskTreeService builds the four-source merged task tree.
type TaskTreeService struct {
	db       *gorm.DB
	registry *orchestrator.Registry
	lockMgr  *lock.Manager
	configSvc *ConfigService
	scheduleSvc *ScheduleService
}

// NewTaskTreeService creates a new task tree service.
func NewTaskTreeService(db *gorm.DB, registry *orchestrator.Registry, lockMgr *lock.Manager, configSvc *ConfigService, scheduleSvc *ScheduleService) *TaskTreeService {
	return &TaskTreeService{
		db:         db,
		registry:   registry,
		lockMgr:    lockMgr,
		configSvc:  configSvc,
		scheduleSvc: scheduleSvc,
	}
}

// TaskTree represents the complete task tree.
type TaskTree struct {
	Accounts    []AccountEntry     `json:"accounts"`
	ActiveLocks []lock.LockInfo    `json:"active_locks"`
}

// AccountEntry represents an account in the task tree.
type AccountEntry struct {
	Name      string         `json:"name"`
	AccountID string         `json:"account_id"`
	Regions   []RegionEntry  `json:"regions"`
}

// RegionEntry represents a region in the task tree.
type RegionEntry struct {
	Code           string         `json:"code"`
	Endpoint       string         `json:"endpoint"`
	Cron           string         `json:"cron"`
	Concurrency    int            `json:"concurrency"`
	Enabled        bool           `json:"enabled"`
	ScheduleEnabled bool          `json:"schedule_enabled"`
	ScheduleCron   string         `json:"schedule_cron"`
	ScheduleName   string         `json:"schedule_name"`
	ResourceGroups []GroupEntry   `json:"resource_groups"`
}

// GroupEntry represents a resource group in the task tree.
type GroupEntry struct {
	Name          string          `json:"name"`
	Resources     []ResourceEntry `json:"resources"`
	Relationships []RelationEntry `json:"relationships"`
}

// ResourceEntry represents a resource in the task tree.
type ResourceEntry struct {
	Name          string `json:"name"`
	Cron          string `json:"cron"`
	Enabled       bool   `json:"enabled"`
	PeriodicID    *int64 `json:"periodic_id"`
	PeriodicName  string `json:"periodic_name"`
	ScheduleExists bool  `json:"schedule_exists"`
}

// RelationEntry represents a relation in the task tree.
type RelationEntry struct {
	Source        string `json:"source"`
	Target        string `json:"target"`
	Cardinality   string `json:"cardinality"`
	Key           string `json:"key"`
	Description   string `json:"description"`
	Cron          string `json:"cron"`
	Enabled       bool   `json:"enabled"`
	PeriodicID    *int64 `json:"periodic_id"`
	PeriodicName  string `json:"periodic_name"`
	ScheduleExists bool  `json:"schedule_exists"`
}

// BuildTaskTree constructs the four-source merged task tree.
func (s *TaskTreeService) BuildTaskTree(ctx context.Context) (*TaskTree, error) {
	accounts, err := s.configSvc.ListAccountRegions(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to list account regions: %w", err)
	}

	scheduleMap := s.scheduleSvc.GetScheduleStatusMap(ctx)
	activeLocks := s.lockMgr.ListActive(ctx)

	var accountEntries []AccountEntry
	for _, acct := range accounts {
		accountEntry := AccountEntry{
			Name:      acct.Name,
			AccountID: acct.AccountID,
		}

		for _, reg := range acct.Regions {
			regionCode := reg.Code
			regionStatus := s.getScheduleStatus(scheduleMap, acct.Name, regionCode, "_region", "dispatch")

			groups := []GroupEntry{}
			for _, g := range s.registry.ListGroups() {
				resources := []ResourceEntry{}
				for _, res := range g.Resources {
					st := s.getScheduleStatus(scheduleMap, acct.Name, regionCode, g.Name, res.Name)
					resources = append(resources, ResourceEntry{
						Name:          res.Name,
						Cron:          st.Cron,
						Enabled:       st.Enabled,
						PeriodicID:    st.PeriodicID,
						PeriodicName:  st.PeriodicName,
						ScheduleExists: st.ScheduleExists,
					})
				}

				relationships := []RelationEntry{}
				for _, rel := range s.registry.GroupRelations(g.Name) {
					tt := fmt.Sprintf("%s_%s", rel.Source, rel.Target)
					st := s.getScheduleStatus(scheduleMap, acct.Name, regionCode, g.Name, tt)
					relationships = append(relationships, RelationEntry{
						Source:        rel.Source,
						Target:        rel.Target,
						Cardinality:   rel.Cardinality,
						Key:           rel.Key,
						Description:   rel.Description,
						Cron:          st.Cron,
						Enabled:       st.Enabled,
						PeriodicID:    st.PeriodicID,
						PeriodicName:  st.PeriodicName,
						ScheduleExists: st.ScheduleExists,
					})
				}

				groups = append(groups, GroupEntry{
					Name:          g.Name,
					Resources:     resources,
					Relationships: relationships,
				})
			}

			accountEntry.Regions = append(accountEntry.Regions, RegionEntry{
				Code:           regionCode,
				Endpoint:       reg.Endpoint,
				Cron:           reg.Cron,
				Concurrency:    reg.Concurrency,
				Enabled:        reg.Enabled,
				ScheduleEnabled: regionStatus.Enabled,
				ScheduleCron:   regionStatus.Cron,
				ScheduleName:   regionStatus.PeriodicName,
				ResourceGroups: groups,
			})
		}
		accountEntries = append(accountEntries, accountEntry)
	}

	return &TaskTree{
		Accounts:    accountEntries,
		ActiveLocks: activeLocks,
	}, nil
}

type scheduleStatus struct {
	Cron          string
	Enabled       bool
	PeriodicID    *int64
	PeriodicName  string
	ScheduleExists bool
}

func (s *TaskTreeService) getScheduleStatus(scheduleMap map[string]*model.PeriodicTask, account, region, group, name string) scheduleStatus {
	periodicName := fmt.Sprintf("%s-%s-%s-%s", account, region, group, name)
	pt, ok := scheduleMap[periodicName]
	if !ok {
		return scheduleStatus{
			PeriodicName:  periodicName,
			ScheduleExists: false,
		}
	}
	return scheduleStatus{
		Cron:          pt.Crontab,
		Enabled:       pt.Enabled,
		PeriodicID:    &pt.ID,
		PeriodicName:  periodicName,
		ScheduleExists: true,
	}
}
