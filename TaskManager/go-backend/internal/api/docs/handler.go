package docs

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/gin-gonic/gin"
)

// Handler holds docs API handlers.
type Handler struct {
	docsDir string
}

// NewHandler creates a new docs handler.
func NewHandler(docsDir string) *Handler {
	// Resolve to absolute path for security checks
	absDir, err := filepath.Abs(docsDir)
	if err != nil {
		absDir = docsDir
	}
	return &Handler{docsDir: absDir}
}

// RegisterRoutes registers all docs routes.
func (h *Handler) RegisterRoutes(rg *gin.RouterGroup) {
	docs := rg.Group("/docs")
	{
		docs.GET("/", h.List)
		docs.GET("/:filename", h.Detail)
	}
}

// DocEntry represents a document entry.
type DocEntry struct {
	Filename string `json:"filename"`
	Title    string `json:"title"`
	Size     int64  `json:"size"`
	SizeHuman string `json:"size_human"`
	Modified string `json:"modified"`
}

var titleRe = regexp.MustCompile(`(?i)<title[^>]*>(.*?)</title>`)

// extractTitle reads the first 4KB of an HTML file and extracts the <title> tag.
func extractTitle(filePath, filename string) string {
	f, err := os.Open(filePath)
	if err != nil {
		return filenameToFallbackTitle(filename)
	}
	defer f.Close()

	buf := make([]byte, 4096)
	n, _ := f.Read(buf)
	if n == 0 {
		return filenameToFallbackTitle(filename)
	}

	if match := titleRe.FindSubmatch(buf[:n]); len(match) > 1 {
		title := strings.TrimSpace(string(match[1]))
		if title != "" {
			return title
		}
	}
	return filenameToFallbackTitle(filename)
}

func filenameToFallbackTitle(filename string) string {
	name := strings.TrimSuffix(filename, filepath.Ext(filename))
	name = strings.ReplaceAll(name, "-", " ")
	name = strings.ReplaceAll(name, "_", " ")
	return strings.Title(name)
}

func humanSize(size int64) string {
	units := []string{"B", "KB", "MB", "GB"}
	s := float64(size)
	for _, unit := range units {
		if s < 1024 {
			if unit == "B" {
				return fmt.Sprintf("%.0f %s", s, unit)
			}
			return fmt.Sprintf("%.1f %s", s, unit)
		}
		s /= 1024
	}
	return fmt.Sprintf("%.1f GB", s)
}

// List returns the list of available HTML documents.
func (h *Handler) List(c *gin.Context) {
	entries, err := os.ReadDir(h.docsDir)
	if err != nil {
		c.JSON(http.StatusOK, gin.H{"docs": []DocEntry{}, "total": 0})
		return
	}

	var docs []DocEntry
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		name := entry.Name()
		// Only HTML files (not .md)
		if !strings.HasSuffix(strings.ToLower(name), ".html") &&
			!strings.HasSuffix(strings.ToLower(name), ".htm") {
			continue
		}

		info, err := entry.Info()
		if err != nil {
			continue
		}

		filePath := filepath.Join(h.docsDir, name)
		title := extractTitle(filePath, name)

		docs = append(docs, DocEntry{
			Filename:  name,
			Title:     title,
			Size:      info.Size(),
			SizeHuman: humanSize(info.Size()),
			Modified:  info.ModTime().Format("2006-01-02 15:04"),
		})
	}

	c.JSON(http.StatusOK, gin.H{"docs": docs, "total": len(docs)})
}

// Detail returns the content of a single document.
func (h *Handler) Detail(c *gin.Context) {
	filename := c.Param("filename")
	filePath := filepath.Join(h.docsDir, filename)

	// Security: ensure the file is within the docs directory
	absPath, err := filepath.Abs(filePath)
	if err != nil || !strings.HasPrefix(absPath, filepath.Clean(h.docsDir)) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			c.JSON(http.StatusNotFound, gin.H{"error": "文档不存在"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	ext := strings.ToLower(filepath.Ext(filename))
	mime := "text/plain"
	switch ext {
	case ".html":
		mime = "text/html"
	case ".md":
		mime = "text/markdown"
	case ".json":
		mime = "application/json"
	}

	c.JSON(http.StatusOK, gin.H{
		"content":  string(content),
		"mime":     mime,
		"filename": filename,
	})
}
