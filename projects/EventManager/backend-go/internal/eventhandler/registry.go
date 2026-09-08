// Package eventhandler provides handler registration and lifecycle management.
// Shared types (Handler, HandlerResult, Registry, etc.) live in the
// eventhandler/types sub-package to avoid import cycles.
//
// This file re-exports the types for convenience so callers can use
// eventhandler.Handler, eventhandler.NewRegistry(), etc. directly.
package eventhandler

import "event-flow/internal/eventhandler/types"

type (
	HandlerResult     = types.HandlerResult
	Handler           = types.Handler
	HandlerFactory    = types.HandlerFactory
	EventTypeMetadata = types.EventTypeMetadata
)

var (
	ErrHandlerNotFound = types.ErrHandlerNotFound
	DefaultRegistry    = types.DefaultRegistry
)

func NewRegistry() *types.Registry { return types.NewRegistry() }

func RegisterMetadata(pattern string, meta types.EventTypeMetadata) {
	types.DefaultRegistry.RegisterMetadata(pattern, meta)
}

func GetAllMetadata() []types.EventTypeMetadata {
	return types.DefaultRegistry.GetAllMetadata()
}
