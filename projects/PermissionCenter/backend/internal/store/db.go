// Package store 数据访问层（GORM + Redis）
package store

import (
	"log"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// Open 建立 PostgreSQL 连接并 AutoMigrate（零手写 SQL，随启动自动建表）
func Open(dsn string) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn),
	})
	if err != nil {
		return nil, err
	}
	if err := db.AutoMigrate(
		&model.User{}, &model.Group{}, &model.UserGroup{},
		&model.App{}, &model.Client{}, &model.AppOwner{},
		&model.Action{}, &model.PermissionTemplate{}, &model.TemplateAction{},
		&model.GroupPermission{},
		&model.Policy{}, &model.PolicyVersion{},
		&model.CapabilityManifest{}, &model.CapabilityAction{}, &model.PolicyTemplate{},
		&model.ScopeOption{},
		&model.AccessRequest{}, &model.ApprovalTask{}, &model.RevokeRequest{},
		&model.CapabilityPublishTask{},
		&model.ResourceModel{}, &model.ResourceInstance{},
		&model.DataContract{}, &model.PatrolLog{},
		&model.SyncJob{}, &model.Bundle{}, &model.AgentStatus{},
		&model.AuditLog{}, &model.DecisionLog{},
	); err != nil {
		return nil, err
	}
	log.Println("[store] AutoMigrate done")
	return db, nil
}
