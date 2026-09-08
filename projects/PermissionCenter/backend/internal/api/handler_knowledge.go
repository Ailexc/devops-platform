// 系统知识库：文档目录 + HTML 文档内容
// GET /api/v1/knowledge/docs        → { categories, items }
// GET /api/v1/knowledge/docs/:id    → { id, title, category, html }
package api

import (
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/knowledge"
)

// listKnowledgeDocs 文档目录（按分类分组）
func (d *Deps) listKnowledgeDocs(c *gin.Context) {
	cats, docs, err := knowledge.Categories()
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"categories": cats, "items": docs})
}

// getKnowledgeDoc 单个文档内容（HTML）
func (d *Deps) getKnowledgeDoc(c *gin.Context) {
	id := strings.TrimSpace(c.Param("id"))
	content, err := knowledge.Content(id)
	if err != nil {
		c.JSON(404, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"id": id, "html": content})
}
