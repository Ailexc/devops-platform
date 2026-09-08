package tasklab

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"
	"gorm.io/datatypes"
	"gorm.io/gorm"

	"event-flow/internal/model"
)

// FastTaskResult holds the outcome of FetchAndProcess.
type FastTaskResult struct {
	TaskID   string      `json:"task_id"`
	EventIDs []string    `json:"event_ids"`
	FilePath string      `json:"file_path"`
	Stats    *FetchStats `json:"stats"`
}

// FetchStats contains word-frequency and field extraction statistics.
type FetchStats struct {
	TotalPosts    int            `json:"total_posts"`
	UniqueWords  int            `json:"unique_words"`
	TopWords     []WordCount    `json:"top_words"`
	FieldsExtracted []string     `json:"fields_extracted"`
}

// WordCount is a word + its frequency.
type WordCount struct {
	Word  string `json:"word"`
	Count int    `json:"count"`
}

// FetchAndProcess fetches posts from JSONPlaceholder, performs word frequency
// analysis, writes an output JSON file, creates an Event record, and reports
// progress to Redis.
func FetchAndProcess(ctx context.Context, db *gorm.DB, store *StatusStore, outputDir string, taskID string, batchIndex int, totalBatches int, batchID string) (*FastTaskResult, error) {
	// ── Create Event at START (so batch_id is searchable immediately) ─
	now := time.Now()
	event := &model.Event{
		ID:         uuid.New(),
		EventType:  "demo.fetch_posts",
		Source:     "test-lab",
		DetailType: "fast-task",
		ResourceID: "test-lab-demo.fetch_posts",
		RawPayload: datatypes.JSON(mustMarshal(map[string]interface{}{
			"batch":    batchIndex,
			"total":    totalBatches,
			"task_id":  taskID,
			"batch_id": batchID,
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
	_ = db.WithContext(ctx).Create(&model.EventLog{EventID: event.ID, Action: "received", Detail: datatypes.JSON(mustMarshal(map[string]interface{}{"source": "test-lab", "trigger": "test-lab"})), CreatedAt: now}).Error
	_ = db.WithContext(ctx).Create(&model.EventLog{EventID: event.ID, Action: "processing", Detail: datatypes.JSON(mustMarshal(map[string]interface{}{"worker": "go-worker"})), CreatedAt: now}).Error

	// ── Step 1: Fetch posts ──────────────────────────────────
	reportProgress(ctx, store, taskID, "fetching", 0.1, fmt.Sprintf("批次 %d/%d: 正在获取帖子数据...", batchIndex, totalBatches))

	posts, err := fetchPosts()
	if err != nil {
		return nil, fmt.Errorf("fetch posts: %w", err)
	}

	reportProgress(ctx, store, taskID, "fetched", 0.4, fmt.Sprintf("成功获取 %d 篇帖子", len(posts)))

	// ── Step 2: Extract fields & word frequency ─────────────
	stats := analysePosts(posts)
	reportProgress(ctx, store, taskID, "analysed", 0.6, fmt.Sprintf("分析完成，共 %d 个唯一词汇", stats.UniqueWords))

	// ── Step 3: Write output JSON ───────────────────────────
	timestamp := time.Now().Format("20060102_150405")
	filename := fmt.Sprintf("fetched_posts_%s_%s_%03d.json", batchID, timestamp, batchIndex)

	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return nil, fmt.Errorf("mkdir output: %w", err)
	}

	filePath := filepath.Join(outputDir, filename)
	output := map[string]interface{}{
		"task_id":  taskID,
		"batch_id": batchID,
		"batch":    batchIndex,
		"posts":    posts,
		"stats":    stats,
	}

	b, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("marshal output: %w", err)
	}
	if err := os.WriteFile(filePath, b, 0o644); err != nil {
		return nil, fmt.Errorf("write file: %w", err)
	}

	reportProgress(ctx, store, taskID, "written", 0.8, fmt.Sprintf("结果已写入 %s", filename))

	// ── Update Event to completed ──────────────────────────────
	completedAt := time.Now()
	if err := db.WithContext(ctx).Model(event).Updates(map[string]interface{}{
		"status":       model.StatusCompleted,
		"processed_at": completedAt,
		"raw_payload":  datatypes.JSON(mustMarshal(map[string]interface{}{
			"batch":           batchIndex,
			"total":           totalBatches,
			"task_id":         taskID,
			"batch_id":        batchID,
			"output_filename": filename,
			"total_posts":     len(posts),
			"top_words":       stats.TopWords,
			"source_url":      "https://jsonplaceholder.typicode.com/posts",
		})),
	}).Error; err != nil {
		return nil, fmt.Errorf("update event: %w", err)
	}

	// Write COMPLETED log
	_ = db.WithContext(ctx).Create(&model.EventLog{
		EventID:   event.ID,
		Action:    "completed",
		Detail:    datatypes.JSON(mustMarshal(map[string]interface{}{
			"result":          fmt.Sprintf("Fetched %d posts, %d unique words", len(posts), stats.UniqueWords),
			"output_filename": filename,
			"total_posts":     len(posts),
			"top_words":       stats.TopWords,
		})),
		CreatedAt: completedAt,
	}).Error

	reportProgress(ctx, store, taskID, "completed", 1.0, "任务完成 ✓")

	return &FastTaskResult{
		TaskID:   taskID,
		EventIDs: []string{event.ID.String()},
		FilePath: filePath,
		Stats:    stats,
	}, nil
}

// ── helpers ──────────────────────────────────────────────────

type jsonPlaceholderPost struct {
	UserID int    `json:"userId"`
	ID     int    `json:"id"`
	Title  string `json:"title"`
	Body   string `json:"body"`
}

func fetchPosts() ([]jsonPlaceholderPost, error) {
	resp, err := http.Get("https://jsonplaceholder.typicode.com/posts")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var posts []jsonPlaceholderPost
	if err := json.Unmarshal(body, &posts); err != nil {
		return nil, err
	}
	return posts, nil
}

func analysePosts(posts []jsonPlaceholderPost) *FetchStats {
	wordFreq := map[string]int{}

	for _, p := range posts {
		extractFields := []string{"title", "body"}
		_ = extractFields // just for documentation
		words := strings.Fields(strings.ToLower(p.Title + " " + p.Body))
		for _, w := range words {
			w = strings.Trim(w, ".,!?;:\"'()-")
			if w == "" {
				continue
			}
			wordFreq[w]++
		}
	}

	// Convert to sorted slice
	wc := make([]WordCount, 0, len(wordFreq))
	for word, count := range wordFreq {
		wc = append(wc, WordCount{Word: word, Count: count})
	}
	sort.Slice(wc, func(i, j int) bool { return wc[i].Count > wc[j].Count })

	if len(wc) > 20 {
		wc = wc[:20]
	}

	return &FetchStats{
		TotalPosts:     len(posts),
		UniqueWords:   len(wordFreq),
		TopWords:      wc,
		FieldsExtracted: []string{"userId", "id", "title", "body"},
	}
}

func reportProgress(ctx context.Context, store *StatusStore, taskID, status string, pct float64, message string) {
	if store == nil {
		return
	}
	progress := map[string]interface{}{
		"status":   status,
		"progress": pct,
		"message":  message,
		"time":     time.Now().Format(time.RFC3339),
	}
	if err := store.SetProgress(ctx, taskID, progress); err != nil {
		log.Printf("tasklab: failed to report progress for %s: %v", taskID, err)
	}
}

func mustMarshal(v interface{}) []byte {
	b, _ := json.Marshal(v)
	return b
}
