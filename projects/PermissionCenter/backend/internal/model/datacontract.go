package model

import "time"

// DataContract 数据契约（注册期模型，清单 A2：勾选数据级验证的能力包发布必填）。
// 主词"数据契约（Data Contract）"，"指纹契约"= 其指纹义务部分（字段+算法档位）的通称；
// 新鲜度承诺 StalenessSlaSec 是 A6 超龄判定（fresh_age > degrade_max_age）的读参来源。
// 出路（红线成文）：发布方字段算不出三元素确定性指纹 → 不勾数据级、只做接口级发布。
type DataContract struct {
	Base
	AppID            uint64   `gorm:"index;not null" json:"app_id"`                  // 能力包归属应用
	ModelCode        string   `gorm:"size:128;index;not null" json:"model"`          // 数据域（资源模型 code，如 host）
	Fields           []string `gorm:"type:jsonb;serializer:json" json:"fields"`      // 指纹字段（发布方声明，注册期试算自检）
	Algorithm        string   `gorm:"size:16;not null" json:"algorithm"`             // 算法档位：L1 / L2 / L3
	StalenessSlaSec  int      `gorm:"not null;default:300" json:"staleness_sla_sec"` // 新鲜度承诺（秒）——发布方签的
	DegradeMaxAgeSec int      `gorm:"not null;default:0" json:"degrade_max_age_sec"` // 降级容忍上限（秒；0 = SLA×K，K 默认 6）
	Enabled          bool     `gorm:"not null;default:true" json:"enabled"`
	// 确认制时钟（清单 2.3.1）：同步成功落地 或 指纹比对一致 才刷新——不是"写入制"。
	// 上游无变更时指纹每次都匹配、时钟持续刷新 → 不会误判为太旧。
	LastConfirmedFreshAt *time.Time `json:"last_confirmed_fresh_at"`
}

// PatrolLog 巡检日志（失败历史，清单 2.3.1）：判定不进、观测与告警分级进——
// 判定只认 fresh_age（时间），不数版本（版本号是发布方自编的、可能跳号，算术不可靠）。
type PatrolLog struct {
	Base
	Domain           string    `gorm:"size:128;index;not null" json:"domain"`
	At               time.Time `gorm:"index" json:"at"`
	Reachable        bool      `json:"reachable"`         // 上游指纹端点是否可达
	FingerprintMatch bool      `json:"fingerprint_match"` // 指纹是否一致（确认"无新数据"）
	SyncOK           bool      `json:"sync_ok"`           // 失配后的增量同步是否成功
	FreshAgeSec      int       `json:"fresh_age_sec"`     // 巡检时点的新鲜度年龄（观测字段）
}
