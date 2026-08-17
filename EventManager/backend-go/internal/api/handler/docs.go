package handler

import (
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/gin-gonic/gin"
)

// DocsHandler holds dependencies for the documentation endpoints.
type DocsHandler struct {
	DocsDir string
}

// NewDocsHandler creates a new DocsHandler.
func NewDocsHandler(docsDir string) *DocsHandler {
	return &DocsHandler{DocsDir: docsDir}
}

// DocInfo represents metadata about a single documentation file.
type DocInfo struct {
	Filename    string `json:"filename"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Size        int64  `json:"size"`
	ModifiedAt  string `json:"modified_at"`
}

// ListDocs handles GET /api/v1/docs
func (h *DocsHandler) ListDocs(c *gin.Context) {
	dir := h.DocsDir
	if dir == "" {
		c.JSON(http.StatusOK, []DocInfo{})
		return
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		c.JSON(http.StatusOK, []DocInfo{})
		return
	}

	result := make([]DocInfo, 0)
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".html") {
			continue
		}

		filePath := filepath.Join(dir, entry.Name())
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

	c.JSON(http.StatusOK, result)
}

// GetDoc handles GET /api/v1/docs/:filename
func (h *DocsHandler) GetDoc(c *gin.Context) {
	filename := c.Param("filename")

	// Security checks: only .html, no path traversal
	if !strings.HasSuffix(filename, ".html") ||
		strings.Contains(filename, "/") ||
		strings.Contains(filename, "\\") ||
		strings.Contains(filename, "..") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "非法文件名"})
		return
	}

	filePath := filepath.Join(h.DocsDir, filename)

	// Ensure the resolved path is still within the docs directory
	absPath, _ := filepath.Abs(filePath)
	absDir, _ := filepath.Abs(h.DocsDir)
	if !strings.HasPrefix(absPath, absDir) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "非法文件路径"})
		return
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "读取文档失败"})
		}
		return
	}

	c.Data(http.StatusOK, "text/html; charset=utf-8", content)
}

// extractMeta extracts title and description from HTML content.
func extractMeta(filename, content string) (string, string) {
	title := strings.TrimSuffix(filename, ".html")

	// Try <title> tag
	titleRe := regexp.MustCompile(`(?i)<title[^>]*>(.*?)</title>`)
	if m := titleRe.FindStringSubmatch(content); len(m) > 1 {
		title = strings.TrimSpace(m[1])
	}

	// Try <meta name="description">
	description := ""
	descRe := regexp.MustCompile(`(?i)<meta\s+name=["']description["']\s+content=["'](.*?)["']`)
	if m := descRe.FindStringSubmatch(content); len(m) > 1 {
		description = strings.TrimSpace(m[1])
	} else {
		// Fallback: first <p> tag
		pRe := regexp.MustCompile(`(?i)<p[^>]*>(.*?)</p>`)
		if m := pRe.FindStringSubmatch(content); len(m) > 1 {
			// Strip HTML tags
			tagRe := regexp.MustCompile(`<[^>]+>`)
			description = strings.TrimSpace(tagRe.ReplaceAllString(m[1], ""))
		}
	}

	if len(description) > 200 {
		description = description[:200]
	}

	return title, description
}
