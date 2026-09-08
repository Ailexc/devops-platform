package types

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"sync"

	"event-flow/internal/model"
)

// ErrHandlerNotFound is returned when no handler matches the event type
var ErrHandlerNotFound = errors.New("event handler not found")

// HandlerResult matches Python's HandlerResult dataclass
type HandlerResult struct {
	Success bool
	Message string
	Data    map[string]interface{}
}

// Handler interface matches Python's BaseEventHandler
type Handler interface {
	Handle(ctx context.Context, event *model.Event) (HandlerResult, error)
	Pattern() string // return the event type pattern this handler matches
}

// HandlerFactory creates a new Handler instance
type HandlerFactory func() Handler

// Registry holds all registered handler factories and metadata
type Registry struct {
	handlers []registryEntry

	mu       sync.RWMutex
	metadata map[string]EventTypeMetadata
}

type registryEntry struct {
	pattern string
	factory HandlerFactory
}

// NewRegistry creates a new empty Registry
func NewRegistry() *Registry {
	return &Registry{
		metadata: make(map[string]EventTypeMetadata),
	}
}

// Register registers a handler factory for a glob pattern
func (r *Registry) Register(pattern string, factory HandlerFactory) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.handlers = append(r.handlers, registryEntry{
		pattern: pattern,
		factory: factory,
	})
}

// Resolve returns a Handler for the given event type.
// It first tries an exact match, then uses filepath.Match for each pattern.
func (r *Registry) Resolve(eventType string) (Handler, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// First pass: exact match
	for _, entry := range r.handlers {
		if entry.pattern == eventType {
			return entry.factory(), nil
		}
	}

	// Second pass: filepath.Match (glob)
	for _, entry := range r.handlers {
		if matched, err := filepath.Match(entry.pattern, eventType); err == nil && matched {
			return entry.factory(), nil
		}
	}

	return nil, fmt.Errorf("%w: %s", ErrHandlerNotFound, eventType)
}

// EventTypeMetadata describes a registered event type for documentation / UI
type EventTypeMetadata struct {
	Category    string
	Icon        string
	Pattern     string
	Description string
	Handler     string

	Events  []map[string]interface{}
	Schema  map[string]interface{}
	Example interface{}
}

// RegisterMetadata stores metadata for a pattern alongside the handler
func (r *Registry) RegisterMetadata(pattern string, meta EventTypeMetadata) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.metadata[pattern] = meta
}

// GetAllMetadata returns all registered metadata
func (r *Registry) GetAllMetadata() []EventTypeMetadata {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]EventTypeMetadata, 0, len(r.metadata))
	for _, meta := range r.metadata {
		result = append(result, meta)
	}
	return result
}

// DefaultRegistry is the global handler registry
var DefaultRegistry = NewRegistry()
