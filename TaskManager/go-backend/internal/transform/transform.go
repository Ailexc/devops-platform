package transform

import (
	"fmt"
	"strings"
)

// Transform converts raw AWS API data to CMDB format.
type Transform struct {
	BindKey string
}

// New creates a new transform with the given bind key.
func New(bindKey string) *Transform {
	return &Transform{BindKey: bindKey}
}

// ToCMDBWithBind converts raw data to CMDB format with bind_key.
func (t *Transform) ToCMDBWithBind(raw map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for k, v := range raw {
		result[k] = v
	}

	// Ensure bind_key is set from cloud_id or the raw bind key field
	if bindVal, ok := result[t.BindKey]; ok && bindVal != "" {
		result["bind_key"] = bindVal
	} else if cloudID, ok := result["cloud_id"].(string); ok && cloudID != "" {
		result["bind_key"] = cloudID
	}

	return result
}

// ToBool converts various truthy/falsy values to bool.
func ToBool(val interface{}) bool {
	switch v := val.(type) {
	case bool:
		return v
	case string:
		return strings.ToLower(v) == "true" || v == "1"
	case int, int64:
		return v != 0
	case float64:
		return v != 0
	default:
		return false
	}
}

// ToString converts various types to string.
func ToString(val interface{}) string {
	if val == nil {
		return ""
	}
	return fmt.Sprintf("%v", val)
}

// ToInt converts various types to int.
func ToInt(val interface{}) int {
	switch v := val.(type) {
	case int:
		return v
	case int64:
		return int(v)
	case float64:
		return int(v)
	case string:
		var n int
		fmt.Sscanf(v, "%d", &n)
		return n
	default:
		return 0
	}
}

// MapKeys returns all keys of a map.
func MapKeys(m map[string]interface{}) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}
