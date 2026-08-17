package breaker

import (
	"time"

	"github.com/sony/gobreaker/v2"
)

// NewCircuitBreaker creates a circuit breaker with sensible defaults for AWS API calls.
func NewCircuitBreaker(name string) *gobreaker.CircuitBreaker[any] {
	return gobreaker.NewCircuitBreaker[any](gobreaker.Settings{
		Name:        name,
		MaxRequests: 3,                // half-open state: allow 3 test requests
		Interval:    60 * time.Second, // clear counts every 60s
		Timeout:     30 * time.Second, // half-open after 30s
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			return counts.ConsecutiveFailures > 5
		},
		OnStateChange: func(name string, from, to gobreaker.State) {
			// Log state transitions
			_ = name
			_ = from
			_ = to
		},
	})
}
