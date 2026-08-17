package worker

import (
	"context"
	"encoding/json"
	"log"

	"github.com/hibiken/asynq"
)

// Dispatcher abstracts task dispatching (allows swapping backends).
type Dispatcher interface {
	Dispatch(ctx context.Context, eventID string) error
}

// AsynqDispatcher sends tasks to asynq (Redis-based).
type AsynqDispatcher struct {
	client *asynq.Client
}

// NewAsynqDispatcher creates a new AsynqDispatcher connected to the given Redis URL.
func NewAsynqDispatcher(redisURL string) *AsynqDispatcher {
	client := asynq.NewClient(asynq.RedisClientOpt{Addr: redisURL})
	return &AsynqDispatcher{client: client}
}

// Dispatch enqueues a process_event task for the given event ID.
func (d *AsynqDispatcher) Dispatch(ctx context.Context, eventID string) error {
	payload, err := json.Marshal(map[string]string{"event_id": eventID})
	if err != nil {
		return err
	}
	task := asynq.NewTask("process_event", payload)
	info, err := d.client.EnqueueContext(ctx, task,
		asynq.Queue("events"),
		asynq.MaxRetry(3),
	)
	if err != nil {
		return err
	}
	log.Printf("Dispatched event %s → asynq task %s", eventID, info.ID)
	return nil
}

// Close shuts down the asynq client.
func (d *AsynqDispatcher) Close() error {
	return d.client.Close()
}

// SyncDispatcher executes synchronously (for offline/demo mode).
type SyncDispatcher struct{}

// Dispatch processes the event inline — useful for tests and single-binary demos.
func (d *SyncDispatcher) Dispatch(ctx context.Context, eventID string) error {
	return ProcessEvent(ctx, eventID)
}
