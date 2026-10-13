package model

// App 应用
// type: 1=api 2=data(cmdb)；openapi_url: OpenAPI 文档地址
// owner_id: 注册者；owner_group_id: 组织兜底锚点（可空）
type App struct {
	Base
	Code         string  `gorm:"size:64;uniqueIndex;not null" json:"code"`
	Name         string  `gorm:"size:128;not null" json:"name"`
	Type         int16   `gorm:"not null;default:1" json:"type"`
	OpenAPIURL   string  `gorm:"size:512" json:"openapi_url"`
	Status       int16   `gorm:"not null;default:1" json:"status"`
	OwnerID      uint64  `json:"owner_id"`
	OwnerGroupID *uint64 `json:"owner_group_id"`
	// 基础信息扩展：描述 / 开发语言
	Description string `gorm:"size:512" json:"description"`
	Language    string `gorm:"size:64" json:"language"`
	// 产品文档 / 操作手册链接（人可读，纯展示，不参与解析）
	DocURL string `gorm:"size:512" json:"doc_url"`
	// 应用版本（详情页/市场展示，如 2.4.1）
	Version string `gorm:"size:32" json:"version"`
	// v12：应用元数据板块 —— 网络信息（Q5）与鉴权方式（D4，展示声明）
	NetInfo JSONMap `gorm:"type:jsonb" json:"net_info"` // 云/账号/区域/VPC/子网/安全组/容器/健康检查接口
	Auth    JSONAny `gorm:"type:jsonb" json:"auth"`     // 鉴权方式列表 [{icon,name,type,strength,desc,meta}]
	// v1.5 T2 通用点查约定（§3.1 应用注册一系统一约定，标配必配）：
	// 回查地址走【系统内部地址】不过网关（中心→业务回调不经网关=零豁免需求）；凭证=M2M 只读
	PermQueryURL   string `gorm:"size:512" json:"perm_query_url"`
	PermQueryToken string `gorm:"size:128" json:"perm_query_token,omitempty"`
}

// Client 程序身份（M2M）：client_id + secret（bcrypt 哈希）
type Client struct {
	Base
	AppID            uint64 `gorm:"index;not null" json:"app_id"`
	ClientID         string `gorm:"size:64;uniqueIndex;not null" json:"client_id"`
	ClientSecretHash string `gorm:"size:255;not null" json:"-"`
	Status           int16  `gorm:"not null;default:1" json:"status"`
	// v12 接入申请（Phase 6.5）：凭证绑定的鉴权方式与目标提供方
	AuthMethod     string `gorm:"size:32" json:"auth_method"`     // oauth2_client_credentials / static_token / api_key / ...
	ProviderAppID  uint64 `gorm:"index" json:"provider_app_id"`   // 接入的目标应用（提供方）
}

// AppOwner 应用负责人（≥2 个，失联时组织树向上兜底）
type AppOwner struct {
	Base
	AppID       uint64 `gorm:"uniqueIndex:idx_ao;not null" json:"app_id"`
	UserID      uint64 `gorm:"uniqueIndex:idx_ao;not null" json:"user_id"`
	IsPrimary   bool   `gorm:"default:true" json:"is_primary"`
	RemindCount int    `gorm:"default:0" json:"remind_count"` // 失联提醒计数
}
