// mock-identity：模拟身份源（HR/AD），SCIM 2.0 风格 API
// IAM 通过 Identity Connector 同步用户/组织副本（source=identity 只读），演示身份同步与 JML
package main

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
)

type IdentityUser struct {
	Username    string         `json:"username"`
	DisplayName string         `json:"display_name"`
	Email       string         `json:"email"`
	Attributes  map[string]any `json:"attributes"`
	Status      int16          `json:"status"`
}

type IdentityOrg struct {
	ID       uint64 `json:"id"`
	Name     string `json:"name"`
	ParentID *uint64 `json:"parent_id"`
}

func main() {
	addr := os.Getenv("IDENTITY_HTTP_ADDR")
	if addr == "" {
		addr = ":8091"
	}

	// 种子组织树（与 seed 规范树一致，身份同步按 name+parent 复用本地节点，避免重建孤儿组织）
	root := uint64(1)
	rd := uint64(2)
	rd1 := uint64(53)
	rd2 := uint64(54)
	opsCenter := uint64(55)
	opsPlatform := uint64(56)
	opsApp := uint64(57)
	orgs := []IdentityOrg{
		{ID: root, Name: "总公司"},
		{ID: rd, Name: "研发中心", ParentID: &root},
		{ID: rd1, Name: "研发一部", ParentID: &rd},
		{ID: rd2, Name: "研发二部", ParentID: &rd},
		{ID: opsCenter, Name: "运维中心", ParentID: &root},
		{ID: opsPlatform, Name: "平台运维部", ParentID: &opsCenter},
		{ID: opsApp, Name: "应用运维部", ParentID: &opsCenter},
	}

	users := []IdentityUser{
		{Username: "alice", DisplayName: "爱丽丝", Email: "alice@corp.com", Attributes: map[string]any{"level": "L3", "dept": "研发一部"}, Status: 1},
		{Username: "bob", DisplayName: "鲍勃", Email: "bob@corp.com", Attributes: map[string]any{"level": "L2", "dept": "研发一部"}, Status: 1},
		{Username: "erin", DisplayName: "艾琳", Email: "erin@corp.com", Attributes: map[string]any{"level": "L3", "dept": "平台运维部"}, Status: 1},
		{Username: "frank", DisplayName: "弗兰克", Email: "frank@corp.com", Attributes: map[string]any{"level": "L3", "dept": "应用运维部"}, Status: 1},
	}

	r := gin.Default()
	r.GET("/healthz", func(g *gin.Context) { g.JSON(200, gin.H{"status": "ok"}) })
	r.GET("/scim/v2/Users", func(g *gin.Context) { g.JSON(200, users) })
	r.GET("/scim/v2/Organizations", func(g *gin.Context) { g.JSON(200, orgs) })

	log.Printf("[mock-identity] listening %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}
