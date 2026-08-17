package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"time"

	"cmdb-go/internal/pkg/cmdbstore"
	"cmdb-go/internal/pkg/result"
	"cmdb-go/internal/tasktypes"

	"github.com/hibiken/asynq"
	"gorm.io/gorm"
)

const outputDir = "/tmp/cmdb_test"

func ensureDir() {
	os.MkdirAll(outputDir, 0755)
}

// TestTaskHandler handles real test task execution.
type TestTaskHandler struct {
	db    *gorm.DB
	store *cmdbstore.Store
}

// NewTestTaskHandler creates a new test task handler.
func NewTestTaskHandler(db *gorm.DB, store *cmdbstore.Store) *TestTaskHandler {
	return &TestTaskHandler{db: db, store: store}
}

// HandleTestTask processes test task execution.
func (h *TestTaskHandler) HandleTestTask(ctx context.Context, t *asynq.Task) error {
	var payload tasktypes.ResourceSyncPayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	switch payload.Resource {
	case "network_collect":
		return h.networkCollect(ctx, payload.ExecutionID)
	case "data_quality_check":
		return h.dataQualityCheck(ctx, payload.ExecutionID)
	case "openlibrary_collect":
		return h.openlibraryCollect(ctx, payload.ExecutionID)
	default:
		return fmt.Errorf("unknown test task: %s", payload.Resource)
	}
}

// networkCollect fetches users from jsonplaceholder API and writes to file.
func (h *TestTaskHandler) networkCollect(ctx context.Context, executionID int64) error {
	ensureDir()
	rb := result.New()
	rb.Log("📡 Phase 1: 请求 jsonplaceholder API")

	// HTTP GET
	url := "https://jsonplaceholder.typicode.com/users"
	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		rb.Log(fmt.Sprintf("❌ 请求失败: %v", err))
		h.finishTask(ctx, executionID, "failed", rb.Build(), err.Error())
		return err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		rb.Log(fmt.Sprintf("❌ 读取响应失败: %v", err))
		h.finishTask(ctx, executionID, "failed", rb.Build(), err.Error())
		return err
	}

	var users []map[string]interface{}
	if err := json.Unmarshal(body, &users); err != nil {
		rb.Log(fmt.Sprintf("❌ 解析 JSON 失败: %v", err))
		h.finishTask(ctx, executionID, "failed", rb.Build(), err.Error())
		return err
	}
	rb.Log(fmt.Sprintf("✅ 获取 %d 条用户数据", len(users)))
	rb.AddStat("fetched", "获取用户数", len(users), "条")

	// Phase 2: Data enrichment
	rb.Log("🧹 Phase 2: 数据清洗（字段裁剪 + 补全同步元数据）")
	enriched := make([]map[string]interface{}, 0, len(users))
	for _, user := range users {
		company, _ := user["company"].(map[string]interface{})
		address, _ := user["address"].(map[string]interface{})
		enriched = append(enriched, map[string]interface{}{
			"id":         user["id"],
			"name":       user["name"],
			"email":      user["email"],
			"company":    company["name"],
			"city":       address["city"],
			"synced_at":  time.Now().Format(time.RFC3339),
		})
	}
	rb.AddStat("enriched", "清洗后数据量", len(enriched), "条")

	// Phase 3: Write to file
	rb.Log("📁 Phase 3: 写入本地文件")
	filename := fmt.Sprintf("%s/sync_network_collect.json", outputDir)
	data, _ := json.MarshalIndent(enriched, "", "  ")
	if err := os.WriteFile(filename, data, 0644); err != nil {
		rb.Log(fmt.Sprintf("❌ 写入文件失败: %v", err))
		h.finishTask(ctx, executionID, "failed", rb.Build(), err.Error())
		return err
	}
	rb.Log(fmt.Sprintf("✅ 文件已保存: %s", filename))
	rb.AddStat("file", "输出文件", filename, "")
	rb.AddStat("size", "文件大小", len(data), "bytes")
	rb.AddArtifact("sync_network_collect.json", filename, "json", int64(len(data)))

	rb.Log("✅ 网络采集完成")
	result := rb.Build()
	result["status"] = "success"
	result["summary"] = fmt.Sprintf("成功采集 %d 条用户数据，已保存到 %s", len(enriched), filename)

	h.finishTask(ctx, executionID, "success", result, "")
	return nil
}

// dataQualityCheck reads CMDB store data and generates a quality report.
func (h *TestTaskHandler) dataQualityCheck(ctx context.Context, executionID int64) error {
	ensureDir()
	rb := result.New()
	rb.Log("📖 Phase 1: 读取 CMDB 演示数据")

	// Read from CMDB store
	resources := []string{"EC2", "VPC", "Subnet", "RDS", "SecurityGroup", "NetworkInterface"}
	var totalCount int64
	moduleStats := make(map[string]int64)

	for _, res := range resources {
		count, _ := h.store.CountByModule(ctx, res)
		moduleStats[res] = count
		totalCount += count
		rb.Log(fmt.Sprintf("  📦 %s: %d 条", res, count))
	}

	rb.AddStat("total", "CMDB 总资源数", totalCount, "条")
	rb.AddStat("modules", "资源模块数", len(resources), "个")

	// Phase 2: Validate
	rb.Log("🔍 Phase 2: 数据完整性校验")
	var issues int
	for _, res := range resources {
		if moduleStats[res] == 0 {
			issues++
			rb.Log(fmt.Sprintf("  ⚠️ %s: 无数据", res))
		}
	}
	rb.AddStat("issues", "问题数", issues, "个")

	// Phase 3: Generate report
	rb.Log("📝 Phase 3: 生成质检报告")
	report := fmt.Sprintf("# CMDB 数据质检报告\n\n生成时间: %s\n\n## 概览\n- 总资源数: %d\n- 资源模块: %d\n- 问题数: %d\n\n## 模块统计\n",
		time.Now().Format("2006-01-02 15:04:05"), totalCount, len(resources), issues)
	for _, res := range resources {
		report += fmt.Sprintf("- %s: %d 条\n", res, moduleStats[res])
	}

	filename := fmt.Sprintf("%s/check_data_quality.md", outputDir)
	if err := os.WriteFile(filename, []byte(report), 0644); err != nil {
		rb.Log(fmt.Sprintf("❌ 写入报告失败: %v", err))
		h.finishTask(ctx, executionID, "failed", rb.Build(), err.Error())
		return err
	}
	rb.Log(fmt.Sprintf("✅ 报告已保存: %s", filename))
	rb.AddStat("report", "质检报告", filename, "")
	reportData, _ := os.ReadFile(filename)
	rb.AddArtifact("check_data_quality.md", filename, "markdown", int64(len(reportData)))

	rb.Log("✅ 数据质检完成")
	result := rb.Build()
	result["status"] = "success"
	result["summary"] = fmt.Sprintf("检查 %d 个模块，共 %d 条资源，发现 %d 个问题", len(resources), totalCount, issues)

	h.finishTask(ctx, executionID, "success", result, "")
	return nil
}

// openlibraryCollect fetches book data from Open Library API and generates analysis.
func (h *TestTaskHandler) openlibraryCollect(ctx context.Context, executionID int64) error {
	ensureDir()
	rb := result.New()

	topics := []struct{ query, label string }{
		{"python", "Python"},
		{"golang", "Go"},
		{"javascript", "JavaScript"},
		{"rust", "Rust"},
		{"database", "Database"},
	}

	rb.Log("📡 Phase 1: 开始采集图书数据")
	allBooks := make([]map[string]interface{}, 0)
	topicCounts := make(map[string]int)
	fetchErrors := make([]string, 0)

	client := &http.Client{Timeout: 20 * time.Second}

	for _, t := range topics {
		rb.Log(fmt.Sprintf("📡 采集主题「%s」...", t.label))
		topicBookCount := 0

		for page := 1; page <= 3; page++ {
			url := fmt.Sprintf("https://openlibrary.org/search.json?q=%s&limit=100&page=%d&fields=key,title,author_name,first_publish_year,edition_count", t.query, page)

			resp, err := client.Get(url)
			if err != nil {
				errMsg := fmt.Sprintf("%s page %d: %v", t.label, page, err)
				rb.Log(fmt.Sprintf("  ❌ page %d/3: 请求失败 — %v", page, err))
				fetchErrors = append(fetchErrors, errMsg)
				time.Sleep(1 * time.Second)
				continue
			}

			if resp.StatusCode != 200 {
				errMsg := fmt.Sprintf("%s page %d: HTTP %d", t.label, page, resp.StatusCode)
				rb.Log(fmt.Sprintf("  ❌ page %d/3: HTTP %d", page, resp.StatusCode))
				fetchErrors = append(fetchErrors, errMsg)
				resp.Body.Close()
				continue
			}

			body, _ := io.ReadAll(resp.Body)
			resp.Body.Close()

			var result struct {
				Docs []struct {
					Key              string   `json:"key"`
					Title            string   `json:"title"`
					AuthorName       []string `json:"author_name"`
					FirstPublishYear int      `json:"first_publish_year"`
					EditionCount     int      `json:"edition_count"`
				} `json:"docs"`
			}
			if err := json.Unmarshal(body, &result); err != nil {
				rb.Log(fmt.Sprintf("  ❌ page %d/3: 解析失败 — %v", page, err))
				fetchErrors = append(fetchErrors, fmt.Sprintf("%s page %d: parse error", t.label, page))
				continue
			}

			for _, doc := range result.Docs {
				authors := doc.AuthorName
				if len(authors) == 0 {
					authors = []string{"Unknown"}
				}
				allBooks = append(allBooks, map[string]interface{}{
					"key":                doc.Key,
					"title":              doc.Title,
					"authors":            authors,
					"first_publish_year": doc.FirstPublishYear,
					"edition_count":      doc.EditionCount,
					"topic":              t.label,
				})
				topicBookCount++
			}
			rb.Log(fmt.Sprintf("  ✅ page %d/3: 获取 %d 条", page, len(result.Docs)))
			time.Sleep(400 * time.Millisecond)
		}

		topicCounts[t.label] = topicBookCount
		rb.Log(fmt.Sprintf("  📊 %s 采集完成: %d 条", t.label, topicBookCount))
	}

	rb.Log(fmt.Sprintf("📡 Phase 1 完成: 共采集 %d 条原始数据", len(allBooks)))
	rb.AddStat("total_raw", "原始采集", len(allBooks), "条")
	rb.AddStat("fetch_errors", "请求失败", len(fetchErrors), "次")

	// If all data sources failed, report failure
	if len(allBooks) == 0 {
		rb.Log("❌ 所有数据源请求失败，任务终止")
		for _, e := range fetchErrors {
			rb.Log(fmt.Sprintf("  - %s", e))
		}
		result := rb.Build()
		result["status"] = "failed"
		result["summary"] = "Open Library 采集失败: " + fetchErrors[0]
		h.finishTask(ctx, executionID, "failed", result, fetchErrors[0])
		return nil
	}

	// Phase 2: Dedup
	rb.Log("🧹 Phase 2: 数据清洗")
	seen := make(map[string]bool)
	uniqueBooks := make([]map[string]interface{}, 0)
	duplicates := 0
	for _, book := range allBooks {
		key, _ := book["key"].(string)
		if key != "" && !seen[key] {
			seen[key] = true
			uniqueBooks = append(uniqueBooks, book)
		} else {
			duplicates++
		}
	}
	rb.Log(fmt.Sprintf("  🔄 去重: %d → %d (去除 %d 重复)", len(allBooks), len(uniqueBooks), duplicates))
	rb.AddStat("total_unique", "去重后", len(uniqueBooks), "本")

	// Phase 3: Analysis
	rb.Log("📊 Phase 3: 多维分析")

	rb.Log("  📈 主题分布:")
	for topic, count := range topicCounts {
		rb.Log(fmt.Sprintf("    %s: %d 本", topic, count))
	}

	// Phase 4: Generate report
	rb.Log("📝 Phase 4: 生成报告")

	report := "# Open Library 图书分析报告\n\n"
	report += fmt.Sprintf("生成时间: %s\n\n", time.Now().Format("2006-01-02 15:04:05"))
	report += "## 采集概览\n"
	report += fmt.Sprintf("- 原始采集: %d 条\n", len(allBooks))
	report += fmt.Sprintf("- 去重后: %d 本\n", len(uniqueBooks))
	report += fmt.Sprintf("- 重复数: %d\n", duplicates)
	report += fmt.Sprintf("- 主题数: %d\n", len(topicCounts))
	report += fmt.Sprintf("- 请求失败: %d 次\n\n", len(fetchErrors))
	report += "## 主题分布\n"
	for topic, count := range topicCounts {
		report += fmt.Sprintf("- %s: %d 本\n", topic, count)
	}

	if len(fetchErrors) > 0 {
		report += "\n## ⚠️ 请求失败记录\n"
		for _, e := range fetchErrors {
			report += fmt.Sprintf("- %s\n", e)
		}
	}

	filename := fmt.Sprintf("%s/openlibrary_report.md", outputDir)
	os.WriteFile(filename, []byte(report), 0644)
	rb.Log(fmt.Sprintf("✅ 报告已保存: %s", filename))

	dataFilename := fmt.Sprintf("%s/openlibrary_data.json", outputDir)
	dataBytes, _ := json.MarshalIndent(uniqueBooks, "", "  ")
	os.WriteFile(dataFilename, dataBytes, 0644)
	rb.Log(fmt.Sprintf("✅ 数据已保存: %s", dataFilename))

	rb.AddArtifact("openlibrary_report.md", filename, "markdown", int64(len(report)))
	rb.AddArtifact("openlibrary_data.json", dataFilename, "json", int64(len(dataBytes)))

	rb.Log("✅ 图书采集分析完成")
	result := rb.Build()
	result["status"] = "success"
	result["summary"] = fmt.Sprintf("采集 %d 条 → 去重 %d 本 (%d 主题)", len(allBooks), len(uniqueBooks), len(topicCounts))

	h.finishTask(ctx, executionID, "success", result, "")
	return nil
}

// finishTask updates the execution record with the result.
func (h *TestTaskHandler) finishTask(ctx context.Context, executionID int64, status string, resultData map[string]interface{}, errMsg string) {
	// Get the record to calculate duration
	var record struct {
		StartedAt time.Time
	}
	h.db.WithContext(ctx).Raw("SELECT started_at FROM execution_records WHERE id = ?", executionID).Scan(&record)

	// Calculate duration
	duration := "-"
	now := time.Now()
	if !record.StartedAt.IsZero() {
		elapsed := now.Sub(record.StartedAt)
		if elapsed < time.Minute {
			duration = fmt.Sprintf("%.1fs", elapsed.Seconds())
		} else {
			mins := int(elapsed.Minutes())
			secs := int(elapsed.Seconds()) % 60
			duration = fmt.Sprintf("%dm%02ds", mins, secs)
		}
	}

	// Update record status
	h.db.WithContext(ctx).Exec(
		"UPDATE execution_records SET status=?, result=?, finished_at=?, error=?, duration=? WHERE id=?",
		status,
		mustMarshal(resultData),
		now,
		errMsg,
		duration,
		executionID,
	)

	slog.Info("test_task: completed",
		"execution_id", executionID,
		"status", status,
		"duration", duration,
	)
}

func mustMarshal(v interface{}) string {
	b, _ := json.Marshal(v)
	return string(b)
}
