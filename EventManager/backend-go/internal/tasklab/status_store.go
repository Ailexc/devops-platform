package tasklab

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

const progressKeyPrefix = "tasklab:progress:"

// StatusStore wraps a Redis client to read/write task progress.
type StatusStore struct {
	rdb *redis.Client
}

// NewStatusStore creates a StatusStore connected to the given Redis client.
func NewStatusStore(rdb *redis.Client) *StatusStore {
	return &StatusStore{rdb: rdb}
}

// SetProgress stores a progress snapshot for the given task ID.
// The progress map is serialised as JSON and written to the key
// tasklab:progress:{taskID} with a 1-hour TTL.
func (s *StatusStore) SetProgress(ctx context.Context, taskID string, progress map[string]interface{}) error {
	b, err := json.Marshal(progress)
	if err != nil {
		return fmt.Errorf("marshal progress: %w", err)
	}
	key := progressKeyPrefix + taskID
	return s.rdb.Set(ctx, key, b, time.Hour).Err()
}

// SetState stores the task state (PENDING/PROGRESS/SUCCESS/FAILURE) and optional meta/result.
func (s *StatusStore) SetState(ctx context.Context, taskID, state string, meta, result map[string]interface{}) error {
	data := map[string]interface{}{
		"state": state,
	}
	if meta != nil {
		data["meta"] = meta
	}
	if result != nil {
		data["result"] = result
	}
	b, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("marshal state: %w", err)
	}
	key := progressKeyPrefix + taskID
	return s.rdb.Set(ctx, key, b, time.Hour).Err()
}

// GetProgress retrieves the latest progress snapshot for the given task ID.
// Returns nil map (without error) when the key does not exist.
func (s *StatusStore) GetProgress(ctx context.Context, taskID string) (map[string]interface{}, error) {
	key := progressKeyPrefix + taskID
	b, err := s.rdb.Get(ctx, key).Bytes()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("get progress: %w", err)
	}
	var progress map[string]interface{}
	if err := json.Unmarshal(b, &progress); err != nil {
		return nil, fmt.Errorf("unmarshal progress: %w", err)
	}
	return progress, nil
}
