package cmdbstore

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

const prefix = "cmdb:store:"

// Store provides Redis-based virtual ORM for CMDB data.
type Store struct {
	rdb *redis.Client
	ttl time.Duration
}

// New creates a new CMDB store.
func New(rdb *redis.Client) *Store {
	return &Store{rdb: rdb, ttl: 7 * 24 * time.Hour} // 7 days retention
}

// Put stores a resource record by module and bind key.
func (s *Store) Put(ctx context.Context, module, bindKey string, data map[string]interface{}) error {
	key := prefix + module + ":" + bindKey
	bytes, err := json.Marshal(data)
	if err != nil {
		return err
	}
	return s.rdb.Set(ctx, key, bytes, s.ttl).Err()
}

// Get retrieves a resource record.
func (s *Store) Get(ctx context.Context, module, bindKey string) (map[string]interface{}, error) {
	key := prefix + module + ":" + bindKey
	bytes, err := s.rdb.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return nil, nil
		}
		return nil, err
	}
	var data map[string]interface{}
	err = json.Unmarshal(bytes, &data)
	return data, err
}

// Delete removes a resource record.
func (s *Store) Delete(ctx context.Context, module, bindKey string) error {
	return s.rdb.Del(ctx, prefix+module+":"+bindKey).Err()
}

// ListByModule returns all resource keys for a module.
func (s *Store) ListByModule(ctx context.Context, module string) ([]string, error) {
	pattern := prefix + module + ":*"
	var keys []string
	iter := s.rdb.Scan(ctx, 0, pattern, 1000).Iterator()
	for iter.Next(ctx) {
		key := iter.Val()
		// Strip prefix to get bind key
		keys = append(keys, key[len(prefix+module)+1:])
	}
	return keys, iter.Err()
}

// ListAllByModule returns all resource records for a module.
func (s *Store) ListAllByModule(ctx context.Context, module string) ([]map[string]interface{}, error) {
	pattern := prefix + module + ":*"
	var results []map[string]interface{}

	iter := s.rdb.Scan(ctx, 0, pattern, 1000).Iterator()
	for iter.Next(ctx) {
		bytes, err := s.rdb.Get(ctx, iter.Val()).Bytes()
		if err != nil {
			continue
		}
		var data map[string]interface{}
		if err := json.Unmarshal(bytes, &data); err != nil {
			continue
		}
		results = append(results, data)
	}
	return results, iter.Err()
}

// CountByModule returns the count of resources for a module.
func (s *Store) CountByModule(ctx context.Context, module string) (int64, error) {
	pattern := prefix + module + ":*"
	var count int64
	iter := s.rdb.Scan(ctx, 0, pattern, 1000).Iterator()
	for iter.Next(ctx) {
		count++
	}
	return count, iter.Err()
}

// TotalCount returns the total count of all CMDB resources.
func (s *Store) TotalCount(ctx context.Context) (int64, error) {
	pattern := prefix + "*"
	var count int64
	iter := s.rdb.Scan(ctx, 0, pattern, 1000).Iterator()
	for iter.Next(ctx) {
		count++
	}
	return count, iter.Err()
}

// Diff compares AWS resources against CMDB and returns adds/updates/deletes.
func (s *Store) Diff(ctx context.Context, module string, awsKeys []string) (adds, updates, deletes []string) {
	cmdbKeys, _ := s.ListByModule(ctx, module)
	cmdbSet := make(map[string]bool)
	for _, k := range cmdbKeys {
		cmdbSet[k] = true
	}
	awsSet := make(map[string]bool)
	for _, k := range awsKeys {
		awsSet[k] = true
	}

	for _, k := range awsKeys {
		if !cmdbSet[k] {
			adds = append(adds, k)
		}
		// Updates would need field-level comparison (simplified here)
	}
	for _, k := range cmdbKeys {
		if !awsSet[k] {
			deletes = append(deletes, k)
		}
	}
	return
}

// BatchPut stores multiple resources at once.
func (s *Store) BatchPut(ctx context.Context, module string, items []map[string]interface{}, bindKeyField string) (int, error) {
	pipe := s.rdb.Pipeline()
	count := 0
	for _, item := range items {
		bindKey, ok := item[bindKeyField].(string)
		if !ok || bindKey == "" {
			continue
		}
		key := prefix + module + ":" + bindKey
		bytes, err := json.Marshal(item)
		if err != nil {
			continue
		}
		pipe.Set(ctx, key, bytes, s.ttl)
		count++
	}
	_, err := pipe.Exec(ctx)
	if err != nil {
		return 0, fmt.Errorf("batch put failed: %w", err)
	}
	return count, nil
}
