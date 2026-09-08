package store

import (
	"context"
	"time"

	"github.com/redis/go-redis/v9"
)

// Cache Redis 封装：策略缓存 / 决策缓存 / 资源热索引 / 事件流
type Cache struct {
	rdb *redis.Client
}

func NewCache(addr string) (*Cache, error) {
	rdb := redis.NewClient(&redis.Options{Addr: addr})
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, err
	}
	return &Cache{rdb: rdb}, nil
}

func (c *Cache) Client() *redis.Client { return c.rdb }

func (c *Cache) Get(ctx context.Context, key string) (string, error) {
	return c.rdb.Get(ctx, key).Result()
}

func (c *Cache) Set(ctx context.Context, key, val string, ttl time.Duration) error {
	return c.rdb.Set(ctx, key, val, ttl).Err()
}

func (c *Cache) Del(ctx context.Context, keys ...string) error {
	return c.rdb.Del(ctx, keys...).Err()
}

// DelPattern 按模式删除（SCAN 迭代，策略变更时使决策缓存失效）
func (c *Cache) DelPattern(ctx context.Context, pattern string) error {
	iter := c.rdb.Scan(ctx, 0, pattern, 200).Iterator()
	for iter.Next(ctx) {
		if err := c.rdb.Del(ctx, iter.Val()).Err(); err != nil {
			return err
		}
	}
	return iter.Err()
}

// CacheEntry 缓存观测条目（键/值/剩余 TTL）
type CacheEntry struct {
	Key   string `json:"key"`
	Value string `json:"value"`
	TTL   int64  `json:"ttl_seconds"`
}

// ScanPattern 扫描模式下的键（含值 + 剩余 TTL），供观测工作台展示
func (c *Cache) ScanPattern(ctx context.Context, pattern string, limit int) ([]CacheEntry, error) {
	var out []CacheEntry
	iter := c.rdb.Scan(ctx, 0, pattern, 200).Iterator()
	for iter.Next(ctx) {
		key := iter.Val()
		val, err := c.rdb.Get(ctx, key).Result()
		if err != nil {
			continue
		}
		ttl, _ := c.rdb.TTL(ctx, key).Result()
		out = append(out, CacheEntry{Key: key, Value: val, TTL: int64(ttl.Seconds())})
		if limit > 0 && len(out) >= limit {
			break
		}
	}
	return out, iter.Err()
}

// CountPattern 统计模式下的键数量
func (c *Cache) CountPattern(ctx context.Context, pattern string) (int64, error) {
	var count int64
	iter := c.rdb.Scan(ctx, 0, pattern, 200).Iterator()
	for iter.Next(ctx) {
		count++
	}
	return count, iter.Err()
}

// XAdd 写事件到 Redis Streams（审计事件 + CMDB webhook 事件统一走流，组件两用）
func (c *Cache) XAdd(ctx context.Context, stream string, values map[string]any) error {
	return c.rdb.XAdd(ctx, &redis.XAddArgs{Stream: stream, Values: values}).Err()
}

func (c *Cache) XRead(ctx context.Context, stream string, count int64) ([]redis.XMessage, error) {
	msgs, err := c.rdb.XRead(ctx, &redis.XReadArgs{
		Streams: []string{stream, "$"},
		Count:   count,
		Block:   time.Second * 2,
	}).Result()
	if err != nil || len(msgs) == 0 {
		return nil, err
	}
	return msgs[0].Messages, nil
}
