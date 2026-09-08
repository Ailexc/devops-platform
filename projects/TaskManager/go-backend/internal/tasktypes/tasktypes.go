package tasktypes

// TaskType constants for asynq task routing
const (
	TaskTypeOrchestrate       = "orchestrator:orchestrate"
	TaskTypeResourceSync      = "worker:resource_sync"
	TaskTypeRelationBuild     = "worker:relation_build"
	TaskTypeScheduledDispatch = "scheduler:dispatch"
	TaskTypeTestTask          = "worker:test_task"
)

// OrchestratePayload holds the payload for orchestration tasks.
type OrchestratePayload struct {
	ExecutionID int64    `json:"execution_id"`
	Account     string   `json:"account"`
	Region      string   `json:"region"`
	Scope       string   `json:"scope"`
	Target      string   `json:"target"`
	Mode        string   `json:"mode"`
	Trigger     string   `json:"trigger"`
	LockID      string   `json:"lock_id"`
	ResourceIDs []string `json:"resource_ids,omitempty"`
}

// ResourceSyncPayload holds the payload for resource sync tasks.
type ResourceSyncPayload struct {
	ExecutionID int64  `json:"execution_id"`
	Account     string `json:"account"`
	Region      string `json:"region"`
	Resource    string `json:"resource"`
	Mode        string `json:"mode"`
}

// RelationBuildPayload holds the payload for relation build tasks.
type RelationBuildPayload struct {
	ExecutionID int64  `json:"execution_id"`
	Account     string `json:"account"`
	Region      string `json:"region"`
	Source      string `json:"source"`
	Target      string `json:"target"`
}

// ScheduledDispatchPayload holds the payload for scheduled dispatch tasks.
type ScheduledDispatchPayload struct {
	Name    string `json:"name"`
	Account string `json:"account"`
	Region  string `json:"region"`
}
