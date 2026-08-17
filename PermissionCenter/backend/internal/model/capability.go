package model

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"time"
)

// 数据范围类型（修正枚举：消除 none 语义歧义）
const (
	ScopeAll       = "all"       // 有接口权限即可，无数据限制
	ScopeOwner     = "owner"     // 仅数据属主（动态判定 / 应用自管）
	ScopeDimension = "dimension" // 按维度过滤（组织 / 标签等）
	ScopeInstance  = "instance"  // 实例勾选
	ScopeNA        = "n/a"       // 不适用（如 create 新建）
)

// 数据操作（对应 HTTP 语义）
const (
	OpList   = "list"
	OpRead   = "read"
	OpCreate = "create"
	OpUpdate = "update"
	OpDelete = "delete"
)

// 能力声明状态
const (
	CapDraft     = "draft"
	CapPublished = "published"
	CapDisabled  = "disabled"
)

// 能力包可见性（v12：owner 自主控制，Q4 定案）
const (
	VisPublic     = "public"
	VisOrgVisible = "org_visible"
	VisHidden     = "hidden"
)

// 预设状态（v12：预设级生命周期，市场只显示 published）
const (
	PresetPublished = "published"
	PresetDraft     = "draft"
)

// 范围选项类型（v12 范围字段类型系统，取代 v10 的 expression/fixed）
const (
	ScopeOptAll         = "all"
	ScopeOptInstance    = "instance"
	ScopeOptSelect      = "select"
	ScopeOptMultiSelect = "multi_select"
	ScopeOptVariable    = "variable"
	ScopeOptInput       = "input"
)

// 自动匹配变量枚举（v12 variable 类型，运行时按 grantee 解析）
const (
	VarCurrentUser    = "@currentUser"
	VarCurrentOrg     = "@currentOrg"
	VarCurrentGroup   = "@currentGroup"
	VarCurrentAccount = "@currentAccount"
)

// 双主体：权限作用主体类型（v12 grantee）
const (
	GranteeUser  = "user"
	GranteeOrg   = "org"
	GranteeGroup = "group"
	GranteeApp   = "app"
)

// CapabilityManifest L1 能力声明：应用声明"我能提供什么、需要什么"
// data_model 可空 = 纯接口能力（大部分系统只有接口授权需求）
// 扩展（能力打包申请流程）：
//   model_fields:     数据模型字段定义 [{name,type,desc,indexed}]，决定哪些条件可用
//   presets:          权限组合预设 [{id,name,status,interfaces,grantee_types,apply_scope,data_control,data_models}]
//   tags:             搜索标签（应用名+数据模型+业务关键词）
// v12 废弃：scope_definitions（范围选项独立表 ScopeOption）、能力包级 data_control（移至预设级）
type CapabilityManifest struct {
	Base
	AppID            uint64      `gorm:"index;not null" json:"app_id"`
	Name             string      `gorm:"size:128;not null" json:"name"`
	DataModel        *string     `gorm:"size:128" json:"data_model"` // 关联数据模型 code（可空=纯接口能力）
	Description      string      `gorm:"size:512" json:"description"`
	Version          int         `gorm:"not null;default:1" json:"version"`
	Status           string      `gorm:"size:16;not null;default:'draft'" json:"status"`
	Visibility       string      `gorm:"size:16;not null;default:'public'" json:"visibility"` // public | org_visible | hidden
	GranteeTypes     StringArray `gorm:"type:jsonb" json:"grantee_types"`                     // 能力包级默认可申请主体
	EnforcementMode  string      `gorm:"size:16;not null;default:'gateway'" json:"enforcement_mode"` // gateway | sdk | both（Q6）
	CreatedBy        uint64      `json:"created_by"`
	UpdatedBy        uint64      `json:"updated_by"`
	ModelFields      JSONAny     `gorm:"type:jsonb" json:"model_fields"`      // 数据模型字段定义
	Presets          JSONAny     `gorm:"type:jsonb" json:"presets"`           // 权限组合预设
	Tags             StringArray `gorm:"type:jsonb" json:"tags"`              // 搜索标签
}

// CapabilityAction 能力 → 权限点 + 数据语义
// allowed_scopes: 支持的数据范围枚举（all/owner/dimension/instance/n-a）
type CapabilityAction struct {
	CapabilityID  uint64 `gorm:"primaryKey" json:"capability_id"`
	ActionID      uint64 `gorm:"primaryKey" json:"action_id"`
	DataOperation string `gorm:"size:16" json:"data_operation"` // list/read/create/update/delete
	AllowedScopes StringArray `gorm:"type:jsonb" json:"allowed_scopes"`
	DefaultScope  string `gorm:"size:16" json:"default_scope"`
	Description   string `gorm:"size:512" json:"description"`
}

// ScopeOption 范围选项（v12 字段类型系统，D1 定案：独立表存储）
// 一个预设 × 一个数据模型 → 一组有序 options（owner 配置 applicant 可选类型）
type ScopeOption struct {
	Base
	CapabilityID uint64  `gorm:"index;not null" json:"capability_id"`
	PresetID     string  `gorm:"index;not null" json:"preset_id"` // 预设 id（字符串，对齐 demo）
	ModelCode    string  `gorm:"index;not null" json:"model_code"`
	Seq          int     `gorm:"not null;default:0" json:"seq"` // 排序
	Type         string  `gorm:"size:24;not null" json:"type"`  // all/instance/select/multi_select/variable/input
	Label        string  `gorm:"size:128" json:"label"`
	Desc         string  `gorm:"size:256" json:"desc"`
	Field        string  `gorm:"size:64" json:"field,omitempty"` // select/multi_select/variable/input
	Op           string  `gorm:"size:16" json:"op,omitempty"`    // 按类型白名单（D6：multi_select 仅 in/!in）
	Choices      JSONAny `gorm:"type:jsonb" json:"choices,omitempty"` // select/multi_select 静态选项 [{label,value}]
	API          string  `gorm:"size:256" json:"api,omitempty"`  // instance 实例列表接口 / select 动态选项接口（D5：仅保留说明）
	Variable     string  `gorm:"size:32" json:"variable,omitempty"` // @currentUser/@currentOrg/@currentGroup/@currentAccount
	VarLabel     string  `gorm:"size:64" json:"var_label,omitempty"`
	Placeholder  string  `gorm:"size:128" json:"placeholder,omitempty"` // input
}

// ScopeOptOps 各类型允许的操作符白名单（对齐 demo 编辑器与 OpenFGA CEL 子集）
func ScopeOptOps(t string) []string {
	switch t {
	case ScopeOptSelect:
		return []string{"==", "!=", "in", "!in"}
	case ScopeOptMultiSelect:
		return []string{"in", "!in"} // D6 定案：仅这两项，保证生成合法 CEL
	case ScopeOptVariable:
		return []string{"==", "!="}
	case ScopeOptInput:
		return []string{"==", "!=", "contains", "startsWith", "in"}
	}
	return nil
}

// ValidScopeOptType 是否为 v12 合法范围选项类型
func ValidScopeOptType(t string) bool {
	switch t {
	case ScopeOptAll, ScopeOptInstance, ScopeOptSelect, ScopeOptMultiSelect, ScopeOptVariable, ScopeOptInput:
		return true
	}
	return false
}

// ValidateScopeOption 结构性校验（field 引用存在性由 handler 结合 ModelFields 校验）
func ValidateScopeOption(o *ScopeOption) error {
	if o == nil {
		return fmt.Errorf("scope option is nil")
	}
	if !ValidScopeOptType(o.Type) {
		return fmt.Errorf("invalid scope option type %q", o.Type)
	}
	if o.Label == "" {
		return fmt.Errorf("scope option label required")
	}
	switch o.Type {
	case ScopeOptSelect, ScopeOptMultiSelect, ScopeOptVariable, ScopeOptInput:
		if o.Field == "" {
			return fmt.Errorf("scope option %q requires field", o.Type)
		}
		if o.Op == "" {
			return fmt.Errorf("scope option %q requires op", o.Type)
		}
		if !containsString(ScopeOptOps(o.Type), o.Op) {
			return fmt.Errorf("op %q not allowed for type %q (allowed: %v)", o.Op, o.Type, ScopeOptOps(o.Type))
		}
	}
	switch o.Type {
	case ScopeOptSelect, ScopeOptMultiSelect:
		if len(o.Choices) == 0 {
			return fmt.Errorf("scope option %q requires non-empty choices", o.Type)
		}
		for i, ch := range o.Choices {
			cm, ok := ch.(map[string]any)
			if !ok {
				return fmt.Errorf("choice %d must be an object {label,value}", i)
			}
			l, _ := cm["label"].(string)
			v, _ := cm["value"].(string)
			if l == "" || v == "" {
				return fmt.Errorf("choice %d requires label and value", i)
			}
		}
	case ScopeOptVariable:
		switch o.Variable {
		case VarCurrentUser, VarCurrentOrg, VarCurrentGroup, VarCurrentAccount:
		default:
			return fmt.Errorf("invalid variable %q (allowed: @currentUser/@currentOrg/@currentGroup/@currentAccount)", o.Variable)
		}
	}
	return nil
}

func containsString(arr []string, s string) bool {
	for _, v := range arr {
		if v == s {
			return true
		}
	}
	return false
}

// PolicyTemplate L3 策略模板：可复用的授权形状（发布到权限市场供申请）
type PolicyTemplate struct {
	Base
	AppID         uint64     `gorm:"index;not null" json:"app_id"`
	Name          string     `gorm:"size:128;not null" json:"name"`
	Description   string     `gorm:"size:512" json:"description"`
	CapabilityID  *uint64    `json:"capability_id"` // 关联能力声明（可空=纯接口模板）
	ActionIDs     JSONArray  `gorm:"type:jsonb" json:"action_ids"`
	DataScope     JSONMap    `gorm:"type:jsonb" json:"data_scope"` // {type: all/owner/dimension/instance, values}
	DefaultScope  string     `gorm:"size:16" json:"default_scope"`
	TTLDays       int        `json:"ttl_days"` // 0=永久
	Effect        int16      `gorm:"not null;default:1" json:"effect"`
	Version       int        `gorm:"not null;default:1" json:"version"`
	Status        string     `gorm:"size:16;not null;default:'draft'" json:"status"`
	PublishedAt   *time.Time `json:"published_at"`
	PublishedBy   uint64     `json:"published_by"`
	ApplyCount    int        `gorm:"default:0" json:"apply_count"`
}

// StringArray 可扫描的 JSONB 字符串数组（如 allowed_scopes）
type StringArray []string

func (s *StringArray) Scan(value any) error {
	if value == nil {
		*s = nil
		return nil
	}
	var b []byte
	switch v := value.(type) {
	case []byte:
		b = v
	case string:
		b = []byte(v)
	default:
		return fmt.Errorf("StringArray scan unsupported type %T", value)
	}
	var arr []string
	if err := json.Unmarshal(b, &arr); err != nil {
		return err
	}
	*s = arr
	return nil
}

func (s StringArray) Value() (driver.Value, error) {
	if s == nil {
		return nil, nil
	}
	return json.Marshal(s)
}
