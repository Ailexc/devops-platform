package tasklab

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"gorm.io/datatypes"
	"gorm.io/gorm"

	"event-flow/internal/model"
)

// SlowTaskResult holds the outcome of GenerateReport.
type SlowTaskResult struct {
	TaskID   string       `json:"task_id"`
	EventIDs []string     `json:"event_ids"`
	FilePath string       `json:"file_path"`
	Report   *ReportData  `json:"report"`
}

// ReportData represents the generated analysis report.
type ReportData struct {
	GeneratedAt   string         `json:"generated_at"`
	DataPoints    int            `json:"data_points"`
	Steps         []StepResult   `json:"steps"`
	Summary       ReportSummary  `json:"summary"`
}

// StepResult describes one analysis step.
type StepResult struct {
	Step    string  `json:"step"`
	Status  string  `json:"status"`
	Value   float64 `json:"value"`
	Elapsed string  `json:"elapsed"`
}

// ReportSummary holds final aggregate metrics.
type ReportSummary struct {
	Mean   float64 `json:"mean"`
	Median float64 `json:"median"`
	StdDev float64 `json:"std_dev"`
	Min    float64 `json:"min"`
	Max    float64 `json:"max"`
}

// GenerateReport simulates a multi-step data analysis pipeline with
// progress reporting. Each step involves a small sleep to mimic real work.
func GenerateReport(ctx context.Context, db *gorm.DB, store *StatusStore, outputDir string, taskID string, batchIndex int, totalBatches int, batchID string) (*SlowTaskResult, error) {
	// ── Create Event at START (so batch_id is searchable immediately) ─
	now := time.Now()
	event := &model.Event{
		ID:         uuid.New(),
		EventType:  "demo.generate_report",
		Source:     "test-lab",
		DetailType: "slow-task",
		ResourceID: "test-lab-demo.generate_report",
		RawPayload: datatypes.JSON(mustMarshal(map[string]interface{}{
			"report_index": batchIndex,
			"total":        totalBatches,
			"task_id":      taskID,
			"batch_id":     batchID,
		})),
		Status:     model.StatusProcessing,
		TraceID:    uuid.New(),
		MaxRetries: 3,
		Handler:    "demo-task",
		WorkerID:   "go-worker",
		ReceivedAt: now,
	}
	if err := db.WithContext(ctx).Create(event).Error; err != nil {
		return nil, fmt.Errorf("create event: %w", err)
	}

	// Write RECEIVED + PROCESSING logs immediately
	_ = db.WithContext(ctx).Create(&model.EventLog{EventID: event.ID, Action: "received", Detail: datatypes.JSON(mustMarshal(map[string]interface{}{"source": "test-lab", "trigger": "test-lab"})), CreatedAt: now}).Error
	_ = db.WithContext(ctx).Create(&model.EventLog{EventID: event.ID, Action: "processing", Detail: datatypes.JSON(mustMarshal(map[string]interface{}{"worker": "go-worker"})), CreatedAt: now}).Error

	reportProgress(ctx, store, taskID, "processing", 0.05, fmt.Sprintf("批次 %d/%d: 开始生成报告...", batchIndex, totalBatches))

	steps := []struct {
		name    string
		pctBase float64
		sleep   time.Duration
	}{
		{"read_data", 0.1, 1 * time.Second},
		{"clean_data", 0.3, 1500 * time.Millisecond},
		{"compute_stats", 0.6, 2 * time.Second},
		{"generate_report", 0.85, 1 * time.Second},
	}

	results := make([]StepResult, 0, len(steps))
	dataPoints := 0
	var values []float64

	for _, s := range steps {
		reportProgress(ctx, store, taskID, "processing", s.pctBase, fmt.Sprintf("执行步骤: %s", s.name))
		start := time.Now()

		// Simulate work
		time.Sleep(s.sleep)

		// Generate fake data for each step
		var val float64
		switch s.name {
		case "read_data":
			dataPoints = 100 + rand.Intn(900)
			val = float64(dataPoints)
		case "clean_data":
			val = float64(dataPoints) * 0.95 // 5% removed
			dataPoints = int(val)
		case "compute_stats":
			values = make([]float64, dataPoints)
			sum := 0.0
			for i := range values {
				values[i] = rand.Float64() * 100
				sum += values[i]
			}
			val = sum / float64(dataPoints) // mean
		case "generate_report":
			val = float64(rand.Intn(50) + 10) // report size in KB
		}

		elapsed := time.Since(start).Truncate(time.Millisecond).String()
		results = append(results, StepResult{
			Step:    s.name,
			Status:  "completed",
			Value:   val,
			Elapsed: elapsed,
		})
	}

	// ── Compute summary statistics ──────────────────────────
	summary := computeSummary(values)
	report := &ReportData{
		GeneratedAt: time.Now().Format(time.RFC3339),
		DataPoints:  dataPoints,
		Steps:       results,
		Summary:     summary,
	}

	// ── Write report JSON ──────────────────────────────────
	timestamp := time.Now().Format("20060102_150405")
	filename := fmt.Sprintf("report_%s_%s_%03d.json", batchID, timestamp, batchIndex)

	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return nil, fmt.Errorf("mkdir output: %w", err)
	}

	filePath := filepath.Join(outputDir, filename)
	b, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("marshal report: %w", err)
	}
	if err := os.WriteFile(filePath, b, 0o644); err != nil {
		return nil, fmt.Errorf("write report: %w", err)
	}

	reportProgress(ctx, store, taskID, "written", 0.92, fmt.Sprintf("报告已写入 %s", filename))

	// ── Update Event to completed ──────────────────────────────
	completedAt := time.Now()
	filenameField := filename
	if err := db.WithContext(ctx).Model(event).Updates(map[string]interface{}{
		"status":       model.StatusCompleted,
		"processed_at": completedAt,
		"raw_payload":  datatypes.JSON(mustMarshal(map[string]interface{}{
			"report_index":     batchIndex,
			"total":            totalBatches,
			"task_id":          taskID,
			"batch_id":         batchID,
			"output_filename":  filenameField,
			"data_points":      dataPoints,
			"steps":            len(results),
		})),
	}).Error; err != nil {
		return nil, fmt.Errorf("update event: %w", err)
	}

	// Write COMPLETED log
	_ = db.WithContext(ctx).Create(&model.EventLog{
		EventID:   event.ID,
		Action:    "completed",
		Detail:    datatypes.JSON(mustMarshal(map[string]interface{}{
			"result":          fmt.Sprintf("Report generated with %d data points in %d steps", dataPoints, len(results)),
			"output_filename": filenameField,
			"data_points":     dataPoints,
			"report_id":       fmt.Sprintf("RPT-%s-%03d", time.Now().Format("20060102"), batchIndex),
			"summary": map[string]interface{}{
				"mean":   summary.Mean,
				"median": summary.Median,
				"min":    summary.Min,
				"max":    summary.Max,
			},
		})),
		CreatedAt: completedAt,
	}).Error

	reportProgress(ctx, store, taskID, "completed", 1.0, "报告生成完成 ✓")

	return &SlowTaskResult{
		TaskID:   taskID,
		EventIDs: []string{event.ID.String()},
		FilePath: filePath,
		Report:   report,
	}, nil
}

// computeSummary calculates basic statistics over a float64 slice.
func computeSummary(vals []float64) ReportSummary {
	if len(vals) == 0 {
		return ReportSummary{}
	}

	sum := 0.0
	min := vals[0]
	max := vals[0]
	for _, v := range vals {
		sum += v
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}
	mean := sum / float64(len(vals))

	// Variance
	varSum := 0.0
	for _, v := range vals {
		d := v - mean
		varSum += d * d
	}
	variance := varSum / float64(len(vals))

	// Median (unsorted – just approximate by sorting copy)
	sorted := make([]float64, len(vals))
	copy(sorted, vals)
	quickSort(sorted)
	median := sorted[len(sorted)/2]

	return ReportSummary{
		Mean:   round4(mean),
		Median: round4(median),
		StdDev: round4(sqrt(variance)),
		Min:    round4(min),
		Max:    round4(max),
	}
}

// quickSort sorts a float64 slice in-place (insertion sort – good enough for <1000 items).
func quickSort(a []float64) {
	for i := 1; i < len(a); i++ {
		key := a[i]
		j := i - 1
		for j >= 0 && a[j] > key {
			a[j+1] = a[j]
			j--
		}
		a[j+1] = key
	}
}

func sqrt(x float64) float64 {
	if x <= 0 {
		return 0
	}
	z := x
	for i := 0; i < 50; i++ {
		z = (z + x/z) / 2
	}
	return z
}

func round4(x float64) float64 {
	return float64(int(x*10000+0.5)) / 10000
}
