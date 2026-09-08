package lock

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/redis/go-redis/v9"
)

const (
	defaultTTL        = 4 * time.Hour
	activeKey         = "cmdb:locks:active"
	setKeyPrefix      = "cmdb:locks:set:"
	metaKeyPrefix     = "cmdb:locks:meta:"
	probeKeyPrefix    = "cmdb:locks:probe:"
)

// Manager implements multi-level concurrency lock using Redis.
type Manager struct {
	rdb *redis.Client
	ttl time.Duration
}

// LockInfo represents an active lock.
type LockInfo struct {
	LockID      string   `json:"lock_id"`
	Account     string   `json:"account"`
	Region      string   `json:"region"`
	Scope       string   `json:"scope"`
	Target      string   `json:"target"`
	StartedAt   string   `json:"started_at"`
	ResourceKeys []string `json:"resource_keys"`
}

// NewManager creates a new lock manager.
func NewManager(rdb *redis.Client) *Manager {
	return &Manager{rdb: rdb, ttl: defaultTTL}
}

func (m *Manager) setKey(lockID string) string { return setKeyPrefix + lockID }
func (m *Manager) metaKey(lockID string) string { return metaKeyPrefix + lockID }

// Acquire attempts to acquire a lock for the given resource keys.
// Returns nil if there is a conflict (409).
func (m *Manager) Acquire(ctx context.Context, account, region string, resourceKeys []string, scope, target string) (*LockInfo, error) {
	keys := uniqueSorted(resourceKeys)
	if len(keys) == 0 {
		return &LockInfo{Account: account, Region: region}, nil
	}

	// Generate lock ID
	lockID := fmt.Sprintf("%s-%s-%d", account, region, time.Now().UnixMilli()%1000000)

	// Check for conflicts with active locks
	activeIDs, err := m.rdb.SMembers(ctx, activeKey).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get active locks: %w", err)
	}

	for _, activeID := range activeIDs {
		// Use temporary key + SINTER to check intersection
		probeKey := probeKeyPrefix + lockID + ":" + activeID
		pipe := m.rdb.Pipeline()
		pipe.SAdd(ctx, probeKey, toStringSlice(keys)...)
		pipe.Expire(ctx, probeKey, 30*time.Second)
		_, err := pipe.Exec(ctx)
		if err != nil {
			continue
		}

		inter, err := m.rdb.SInter(ctx, probeKey, m.setKey(activeID)).Result()
		m.rdb.Del(ctx, probeKey)
		if err != nil {
			continue
		}

		if len(inter) > 0 {
			slog.Info("concurrency_lock: CONFLICT",
				"account", account, "region", region,
				"scope", scope, "target", target,
				"conflict_lock", activeID,
				"shared_resources", len(inter),
			)
			return nil, nil
		}
	}

	// No conflict — acquire lock
	pipe := m.rdb.Pipeline()
	pipe.SAdd(ctx, m.setKey(lockID), toStringSlice(keys)...)
	pipe.Expire(ctx, m.setKey(lockID), m.ttl)

	meta := map[string]interface{}{
		"lock_id":      lockID,
		"account":      account,
		"region":       region,
		"scope":        scope,
		"target":       target,
		"started_at":   time.Now().UTC().Format(time.RFC3339),
		"resource_keys": mustMarshal(keys),
	}
	pipe.HSet(ctx, m.metaKey(lockID), meta)
	pipe.Expire(ctx, m.metaKey(lockID), m.ttl)
	pipe.SAdd(ctx, activeKey, lockID)

	if _, err := pipe.Exec(ctx); err != nil {
		return nil, fmt.Errorf("failed to acquire lock: %w", err)
	}

	return &LockInfo{
		LockID:       lockID,
		Account:      account,
		Region:       region,
		Scope:        scope,
		Target:       target,
		StartedAt:    time.Now().UTC().Format(time.RFC3339),
		ResourceKeys: keys,
	}, nil
}

// Release removes a lock by its ID.
func (m *Manager) Release(ctx context.Context, lockID string) error {
	if lockID == "" {
		return nil
	}
	pipe := m.rdb.Pipeline()
	pipe.Del(ctx, m.setKey(lockID))
	pipe.Del(ctx, m.metaKey(lockID))
	pipe.SRem(ctx, activeKey, lockID)
	_, err := pipe.Exec(ctx)
	return err
}

// ListActive returns all currently active locks.
func (m *Manager) ListActive(ctx context.Context) []LockInfo {
	activeIDs, err := m.rdb.SMembers(ctx, activeKey).Result()
	if err != nil || len(activeIDs) == 0 {
		return nil
	}

	var locks []LockInfo
	for _, id := range activeIDs {
		meta, err := m.rdb.HGetAll(ctx, m.metaKey(id)).Result()
		if err != nil || len(meta) == 0 {
			continue
		}
		info := LockInfo{
			LockID:    meta["lock_id"],
			Account:   meta["account"],
			Region:    meta["region"],
			Scope:     meta["scope"],
			Target:    meta["target"],
			StartedAt: meta["started_at"],
		}
		if rk := meta["resource_keys"]; rk != "" {
			_ = json.Unmarshal([]byte(rk), &info.ResourceKeys)
		}
		locks = append(locks, info)
	}
	return locks
}

// HasConflict checks if the given resource keys conflict with any active lock.
func (m *Manager) HasConflict(ctx context.Context, resourceKeys []string) (bool, string) {
	keys := uniqueSorted(resourceKeys)
	if len(keys) == 0 {
		return false, ""
	}

	activeIDs, err := m.rdb.SMembers(ctx, activeKey).Result()
	if err != nil {
		return false, ""
	}

	for _, activeID := range activeIDs {
		members, err := m.rdb.SMembers(ctx, m.setKey(activeID)).Result()
		if err != nil || len(members) == 0 {
			continue
		}
		memberSet := make(map[string]bool)
		for _, m := range members {
			memberSet[m] = true
		}
		for _, k := range keys {
			if memberSet[k] {
				return true, activeID
			}
		}
	}
	return false, ""
}

func uniqueSorted(s []string) []string {
	seen := make(map[string]bool)
	var result []string
	for _, v := range s {
		if !seen[v] {
			seen[v] = true
			result = append(result, v)
		}
	}
	// Simple sort
	for i := 0; i < len(result); i++ {
		for j := i + 1; j < len(result); j++ {
			if result[i] > result[j] {
				result[i], result[j] = result[j], result[i]
			}
		}
	}
	return result
}

func toStringSlice(s []string) []interface{} {
	result := make([]interface{}, len(s))
	for i, v := range s {
		result[i] = v
	}
	return result
}

func mustMarshal(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
