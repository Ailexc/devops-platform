package worker

import (
	"math"
	"math/rand"
	"time"
)

const (
	baseDelay  = 4 * time.Second
	maxDelay   = 300 * time.Second
)

// BackoffDelay computes the delay before the next retry attempt.
// It mirrors Python's calculate_exponential_backoff:
//
//	delay = min(base * 2^retry_count, max)
//	jitter = random in [50%, 100%] of computed delay
func BackoffDelay(retryCount int) time.Duration {
	if retryCount < 0 {
		retryCount = 0
	}
	delay := float64(baseDelay) * math.Pow(2, float64(retryCount))
	if delay > float64(maxDelay) {
		delay = float64(maxDelay)
	}
	// Apply 50-100% jitter
	jitter := 0.5 + rand.Float64()*0.5 // [0.5, 1.0)
	return time.Duration(delay * jitter)
}
