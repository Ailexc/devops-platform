package model

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
)

// JSONMap 可扫描的 JSONB map（GORM + postgres 对裸 map 扫描不友好，需自定义 Scanner/Valuer）
type JSONMap map[string]any

func (j *JSONMap) Scan(value any) error {
	if value == nil {
		*j = nil
		return nil
	}
	var b []byte
	switch v := value.(type) {
	case []byte:
		b = v
	case string:
		b = []byte(v)
	default:
		return fmt.Errorf("JSONMap scan unsupported type %T", value)
	}
	var m map[string]any
	if err := json.Unmarshal(b, &m); err != nil {
		return err
	}
	*j = m
	return nil
}

func (j JSONMap) Value() (driver.Value, error) {
	if j == nil {
		return nil, nil
	}
	return json.Marshal(j)
}

// JSONArray 可扫描的 JSONB 数组（如 action_ids）
type JSONArray []uint64

func (j *JSONArray) Scan(value any) error {
	if value == nil {
		*j = nil
		return nil
	}
	var b []byte
	switch v := value.(type) {
	case []byte:
		b = v
	case string:
		b = []byte(v)
	default:
		return fmt.Errorf("JSONArray scan unsupported type %T", value)
	}
	var arr []uint64
	if err := json.Unmarshal(b, &arr); err != nil {
		return err
	}
	*j = arr
	return nil
}

func (j JSONArray) Value() (driver.Value, error) {
	if j == nil {
		return nil, nil
	}
	return json.Marshal(j)
}

// JSONAny 可扫描的 JSONB 任意数组（如 presets 数组对象、model_fields 列表）
type JSONAny []any

func (j *JSONAny) Scan(value any) error {
	if value == nil {
		*j = nil
		return nil
	}
	var b []byte
	switch v := value.(type) {
	case []byte:
		b = v
	case string:
		b = []byte(v)
	default:
		return fmt.Errorf("JSONAny scan unsupported type %T", value)
	}
	var arr []any
	if err := json.Unmarshal(b, &arr); err != nil {
		return err
	}
	*j = arr
	return nil
}

func (j JSONAny) Value() (driver.Value, error) {
	if j == nil {
		return nil, nil
	}
	return json.Marshal(j)
}
