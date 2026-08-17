package retry

import (
	"context"
	"fmt"
	"log/slog"
	"math"
	"math/rand"
	"time"
)

// Config defines retry behavior.
type Config struct {
	MaxRetries int
	BaseDelay  time.Duration
	MaxDelay   time.Duration
	Multiplier float64
}

// DefaultConfig returns a sensible default retry config.
func DefaultConfig() Config {
	return Config{
		MaxRetries: 3,
		BaseDelay:  1 * time.Second,
		MaxDelay:   30 * time.Second,
		Multiplier: 2.0,
	}
}

// Do executes fn with retry logic.
func Do(ctx context.Context, cfg Config, fn func(ctx context.Context) error) error {
	var lastErr error

	for attempt := 0; attempt <= cfg.MaxRetries; attempt++ {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("context cancelled: %w", err)
		}

		lastErr = fn(ctx)
		if lastErr == nil {
			return nil
		}

		if attempt < cfg.MaxRetries {
			delay := cfg.computeDelay(attempt)
			slog.Warn("retry: attempt failed, retrying",
				"attempt", attempt+1,
				"max_retries", cfg.MaxRetries,
				"delay", delay,
				"error", lastErr,
			)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(delay):
			}
		}
	}

	return fmt.Errorf("all %d retries exhausted: %w", cfg.MaxRetries, lastErr)
}

func (c Config) computeDelay(attempt int) time.Duration {
	delay := float64(c.BaseDelay) * math.Pow(c.Multiplier, float64(attempt))
	if delay > float64(c.MaxDelay) {
		delay = float64(c.MaxDelay)
	}
	// Add jitter (±20%)
	jitter := delay * 0.2 * (rand.Float64()*2 - 1)
	return time.Duration(delay + jitter)
}
