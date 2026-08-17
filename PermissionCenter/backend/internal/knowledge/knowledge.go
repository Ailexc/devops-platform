// Package knowledge 系统知识库：嵌入 HTML 文档，提供目录与内容读取。
// 文档目录：docs/（本包内 go:embed），元数据 catalog.json 定义目录树。
package knowledge

import (
	"embed"
	"encoding/json"
	"fmt"
)

//go:embed all:docs
var docsFS embed.FS

// Doc 文档目录条目
type Doc struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Category string `json:"category"`
	Summary  string `json:"summary"`
	Order    int    `json:"order"`
	File     string `json:"file"`
}

// Categories 目录按分类分组返回（保持 catalog 顺序）
func Categories() ([]string, []Doc, error) {
	docs, err := Catalog()
	if err != nil {
		return nil, nil, err
	}
	var cats []string
	seen := map[string]bool{}
	for _, d := range docs {
		if !seen[d.Category] {
			seen[d.Category] = true
			cats = append(cats, d.Category)
		}
	}
	return cats, docs, nil
}

// Catalog 读取全部文档目录（按 order 排序）
func Catalog() ([]Doc, error) {
	raw, err := docsFS.ReadFile("docs/catalog.json")
	if err != nil {
		return nil, fmt.Errorf("read catalog: %w", err)
	}
	var docs []Doc
	if err := json.Unmarshal(raw, &docs); err != nil {
		return nil, fmt.Errorf("parse catalog: %w", err)
	}
	return docs, nil
}

// Content 按文档 ID 返回 HTML 内容
func Content(id string) (string, error) {
	docs, err := Catalog()
	if err != nil {
		return "", err
	}
	for _, d := range docs {
		if d.ID == id {
			raw, err := docsFS.ReadFile("docs/" + d.File)
			if err != nil {
				return "", fmt.Errorf("read doc %s: %w", id, err)
			}
			return string(raw), nil
		}
	}
	return "", fmt.Errorf("doc %s not found", id)
}
