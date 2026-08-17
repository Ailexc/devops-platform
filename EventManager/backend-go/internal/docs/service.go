package docs

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// DocInfo represents metadata about a single documentation file.
type DocInfo struct {
	Filename    string `json:"filename"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Size        int64  `json:"size"`
	ModifiedAt  string `json:"modified_at"`
}

// DocsService provides read-only access to the docs directory.
type DocsService struct {
	docsDir string
}

// NewDocsService creates a DocsService rooted at the given directory.
func NewDocsService(docsDir string) *DocsService {
	return &DocsService{docsDir: docsDir}
}

// ListDocs scans the docs directory for .html files and extracts
// <title> and <meta name="description"> content via regex.
func (s *DocsService) ListDocs() ([]DocInfo, error) {
	if s.docsDir == "" {
		return []DocInfo{}, nil
	}

	entries, err := os.ReadDir(s.docsDir)
	if err != nil {
		return nil, fmt.Errorf("read docs dir: %w", err)
	}

	result := make([]DocInfo, 0)
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".html") {
			continue
		}

		filePath := filepath.Join(s.docsDir, entry.Name())
		info, err := entry.Info()
		if err != nil {
			continue
		}

		content, err := os.ReadFile(filePath)
		if err != nil {
			continue
		}

		title, description := extractMeta(entry.Name(), string(content))
		modTime := info.ModTime().Format("2006-01-02 15:04")

		result = append(result, DocInfo{
			Filename:    entry.Name(),
			Title:       title,
			Description: description,
			Size:        info.Size(),
			ModifiedAt:  modTime,
		})
	}

	return result, nil
}

// GetDoc reads a single .html file and returns its raw bytes.
// Security: only .html extension is allowed and path traversal is rejected.
func (s *DocsService) GetDoc(filename string) ([]byte, error) {
	if !strings.HasSuffix(filename, ".html") ||
		strings.Contains(filename, "/") ||
		strings.Contains(filename, "\\") ||
		strings.Contains(filename, "..") {
		return nil, fmt.Errorf("非法文件名")
	}

	filePath := filepath.Join(s.docsDir, filename)

	// Ensure the resolved path stays within the docs directory
	absPath, _ := filepath.Abs(filePath)
	absDir, _ := filepath.Abs(s.docsDir)
	if !strings.HasPrefix(absPath, absDir) {
		return nil, fmt.Errorf("非法文件路径")
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("文档不存在")
		}
		return nil, fmt.Errorf("读取文档失败: %w", err)
	}
	return content, nil
}

// ── regex helpers ──────────────────────────────────────────

var (
	titleRe = regexp.MustCompile(`(?i)<title[^>]*>(.*?)</title>`)
	descRe  = regexp.MustCompile(`(?i)<meta\s+name=["']description["']\s+content=["'](.*?)["']`)
	pRe     = regexp.MustCompile(`(?i)<p[^>]*>(.*?)</p>`)
	tagRe   = regexp.MustCompile(`<[^>]+>`)
)

func extractMeta(filename, content string) (string, string) {
	title := strings.TrimSuffix(filename, ".html")

	if m := titleRe.FindStringSubmatch(content); len(m) > 1 {
		title = strings.TrimSpace(m[1])
	}

	description := ""
	if m := descRe.FindStringSubmatch(content); len(m) > 1 {
		description = strings.TrimSpace(m[1])
	} else if m := pRe.FindStringSubmatch(content); len(m) > 1 {
		description = strings.TrimSpace(tagRe.ReplaceAllString(m[1], ""))
	}

	if len(description) > 200 {
		description = description[:200]
	}

	return title, description
}
