package model

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
)

// hashJSON 规范化哈希：encoding/json 对 map key 排序 → 同一逻辑数据必然得到同一哈希
func hashJSON(v any) string {
	b, err := json.Marshal(v)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

// ComputeInstanceFP 记录级指纹：权限判定所需字段（投影裁剪后的字段）规范化哈希。
// 用途：写库去重（fp 相同不写库）+ 深对账差异定位（哪条变了）。清单 A1。
func ComputeInstanceFP(inst *ResourceInstance) string {
	return hashJSON(struct {
		ExternalID string         `json:"external_id"`
		Name       string         `json:"name"`
		OwnerID    *uint64        `json:"owner_id"`
		Attributes map[string]any `json:"attributes"`
	}{inst.ExternalID, inst.Name, inst.OwnerID, inst.Attributes})
}

// ComputeModelFP 模型定义指纹（A5b 深对账差异定位用）
func ComputeModelFP(m *ResourceModel) string {
	return hashJSON(struct {
		Code   string         `json:"code"`
		Name   string         `json:"name"`
		Schema map[string]any `json:"attributes_schema"`
	}{m.Code, m.Name, m.AttributesSchema})
}
