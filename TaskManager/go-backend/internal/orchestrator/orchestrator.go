package orchestrator

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
)

// WaveKind represents the type of wave.
type WaveKind string

const (
	WaveResource WaveKind = "resource"
	WaveRelation WaveKind = "relation"
)

// WaveState represents the state of a wave.
type WaveState string

const (
	StatePending      WaveState = "pending"
	StateRunning      WaveState = "running"
	StateCompleted    WaveState = "completed"
	StateFailed       WaveState = "failed"
)

// TaskState represents the overall orchestration state.
type TaskState string

const (
	StateWave1Running  TaskState = "wave1_running"
	StateWave2Running  TaskState = "wave2_running"
	StateFinalized     TaskState = "finalized"
)

// Wave tracks the progress of a group of tasks in one wave.
type Wave struct {
	ExecutionID string    `json:"execution_id"`
	Kind        WaveKind  `json:"kind"`
	Total       int       `json:"total"`
	Succeeded   int       `json:"succeeded"`
	Failed      int       `json:"failed"`
	Done        int       `json:"done"`
	State       WaveState `json:"state"`
}

// waveKey returns the Redis key for a wave's counters.
func waveKey(executionID string, kind WaveKind) string {
	return fmt.Sprintf("cmdb:wave:%s:%s", executionID, kind)
}

// Orchestrator drives the two-wave state machine.
type Orchestrator struct {
	db  *gorm.DB
	rdb *redis.Client
}

// NewOrchestrator creates a new orchestrator.
func NewOrchestrator(db *gorm.DB, rdb *redis.Client) *Orchestrator {
	return &Orchestrator{db: db, rdb: rdb}
}

// InitWave initializes a wave in Redis.
func (o *Orchestrator) InitWave(executionID string, kind WaveKind, total int) error {
	wave := Wave{
		ExecutionID: executionID,
		Kind:        kind,
		Total:       total,
		State:       StatePending,
	}
	key := waveKey(executionID, kind)
	bytes, err := json.Marshal(wave)
	if err != nil {
		return err
	}
	return o.rdb.Set(o.ctx(), key, bytes, 4*time.Hour).Err()
}

// OnTaskDone is called when a task in the wave completes.
func (o *Orchestrator) OnTaskDone(executionID string, kind WaveKind, success bool) (*Wave, error) {
	key := waveKey(executionID, kind)

	// Use pipeline for atomic read-modify-write
	pipe := o.rdb.Pipeline()
	incrDone := pipe.HIncrBy(o.ctx(), key+":counters", "done", 1)
	if success {
		pipe.HIncrBy(o.ctx(), key+":counters", "succeeded", 1)
	} else {
		pipe.HIncrBy(o.ctx(), key+":counters", "failed", 1)
	}
	_, err := pipe.Exec(o.ctx())
	if err != nil {
		return nil, err
	}

	// Read current wave state
	waveBytes, err := o.rdb.Get(o.ctx(), key).Bytes()
	if err != nil {
		return nil, err
	}
	var wave Wave
	if err := json.Unmarshal(waveBytes, &wave); err != nil {
		return nil, err
	}

	// Read counters
	counters, err := o.rdb.HGetAll(o.ctx(), key+":counters").Result()
	if err != nil {
		return nil, err
	}

	wave.Done = int(incrDone.Val())
	if s, ok := counters["succeeded"]; ok {
		fmt.Sscanf(s, "%d", &wave.Succeeded)
	}
	if f, ok := counters["failed"]; ok {
		fmt.Sscanf(f, "%d", &wave.Failed)
	}

	// Check if wave is complete
	if wave.Done >= wave.Total {
		wave.State = StateCompleted
		if wave.Succeeded == 0 && wave.Failed > 0 {
			wave.State = StateFailed
		}
		// Save updated state
		waveBytes, _ = json.Marshal(wave)
		o.rdb.Set(o.ctx(), key, waveBytes, 4*time.Hour)
	}

	return &wave, nil
}

// IsWaveComplete checks if a wave has completed.
func (o *Orchestrator) IsWaveComplete(executionID string, kind WaveKind) (bool, *Wave, error) {
	key := waveKey(executionID, kind)
	waveBytes, err := o.rdb.Get(o.ctx(), key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return false, nil, nil
		}
		return false, nil, err
	}
	var wave Wave
	if err := json.Unmarshal(waveBytes, &wave); err != nil {
		return false, nil, err
	}
	return wave.State == StateCompleted || wave.State == StateFailed, &wave, nil
}

// BuildWaves expands scope into resource tasks and relation tasks.
func (o *Orchestrator) BuildWaves(registry *Registry, account, region, scope, target string) (resourceTasks, relationTasks []TaskInfo) {
	switch scope {
	case "region":
		for _, g := range registry.ListGroups() {
			for _, res := range g.Resources {
				resourceTasks = append(resourceTasks, TaskInfo{
					Type:     "resource",
					Name:     res.Name,
					Account:  account,
					Region:   region,
					Resource: res.Name,
				})
			}
			for _, rel := range registry.GroupRelations(g.Name) {
				relationTasks = append(relationTasks, TaskInfo{
					Type:   "relation",
					Name:   fmt.Sprintf("%s→%s", rel.Source, rel.Target),
					Source: rel.Source,
					Target: rel.Target,
				})
			}
		}
	case "group":
		g := registry.GetGroup(target)
		if g != nil {
			for _, res := range g.Resources {
				resourceTasks = append(resourceTasks, TaskInfo{
					Type:     "resource",
					Name:     res.Name,
					Account:  account,
					Region:   region,
					Resource: res.Name,
				})
			}
			for _, rel := range registry.GroupRelations(g.Name) {
				relationTasks = append(relationTasks, TaskInfo{
					Type:   "relation",
					Name:   fmt.Sprintf("%s→%s", rel.Source, rel.Target),
					Source: rel.Source,
					Target: rel.Target,
				})
			}
		}
	case "resource":
		res := registry.GetResource(target)
		if res != nil {
			resourceTasks = append(resourceTasks, TaskInfo{
				Type:     "resource",
				Name:     res.Name,
				Account:  account,
				Region:   region,
				Resource: res.Name,
			})
		}
	case "relation":
		// Parse "source:target"
		var source, tgt string
		for i, c := range target {
			if c == ':' {
				source = target[:i]
				tgt = target[i+1:]
				break
			}
		}
		rel := registry.GetRelation(source, tgt)
		if rel != nil {
			relationTasks = append(relationTasks, TaskInfo{
				Type:   "relation",
				Name:   fmt.Sprintf("%s→%s", rel.Source, rel.Target),
				Source: rel.Source,
				Target: rel.Target,
			})
		}
	}
	return
}

// TaskInfo describes a task to be dispatched.
type TaskInfo struct {
	Type     string `json:"type"`     // "resource" or "relation"
	Name     string `json:"name"`
	Account  string `json:"account,omitempty"`
	Region   string `json:"region,omitempty"`
	Resource string `json:"resource,omitempty"`
	Source   string `json:"source,omitempty"`
	Target   string `json:"target,omitempty"`
}

func (o *Orchestrator) ctx() context.Context {
	return context.Background()
}

// CalculateWaveStatus determines the overall status from wave results.
func CalculateWaveStatus(wave *Wave) string {
	if wave.Failed == 0 {
		return "success"
	}
	if wave.Succeeded == 0 {
		return "failed"
	}
	return "partial"
}
