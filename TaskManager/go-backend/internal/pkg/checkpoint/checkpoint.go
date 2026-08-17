package checkpoint

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

const prefix = "cmdb:checkpoint:"

// Manager provides checkpoint/resume capability for long-running tasks.
type Manager struct {
	rdb *redis.Client
	ttl time.Duration
}

// NewManager creates a new checkpoint manager.
func NewManager(rdb *redis.Client) *Manager {
	return &Manager{rdb: rdb, ttl: 24 * time.Hour}
}

// Save stores a checkpoint for a task.
func (m *Manager) Save(ctx context.Context, taskID string, data map[string]interface{}) error {
	key := prefix + taskID
	bytes, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal checkpoint: %w", err)
	}
	return m.rdb.Set(ctx, key, bytes, m.ttl).Err()
}

// Load retrieves a checkpoint for a task.
func (m *Manager) Load(ctx context.Context, taskID string) (map[string]interface{}, error) {
	key := prefix + taskID
	bytes, err := m.rdb.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to load checkpoint: %w", err)
	}

	var data map[string]interface{}
	if err := json.Unmarshal(bytes, &data); err != nil {
		return nil, fmt.Errorf("failed to unmarshal checkpoint: %w", err)
	}
	return data, nil
}

// Delete removes a checkpoint.
func (m *Manager) Delete(ctx context.Context, taskID string) error {
	return m.rdb.Del(ctx, prefix+taskID).Err()
}
