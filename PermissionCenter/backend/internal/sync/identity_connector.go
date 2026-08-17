package sync

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// IdentityUser mock-identity 用户
type IdentityUser struct {
	Username    string         `json:"username"`
	DisplayName string         `json:"display_name"`
	Email       string         `json:"email"`
	Attributes  map[string]any `json:"attributes"`
	Status      int16          `json:"status"`
}

// IdentityOrg mock-identity 组织节点
type IdentityOrg struct {
	ID       uint64 `json:"id"`
	Name     string `json:"name"`
	ParentID *uint64 `json:"parent_id"`
}

// IdentityConnector 同步 mock-identity 用户/组织（SCIM 风格，source=identity 只读）
type IdentityConnector struct {
	baseURL string
	client  *http.Client
	users   *store.UserRepo
	grps    *store.GroupRepo
	syncs   *store.SyncRepo
}

func NewIdentityConnector(baseURL string, users *store.UserRepo, grps *store.GroupRepo, syncs *store.SyncRepo) *IdentityConnector {
	return &IdentityConnector{
		baseURL: baseURL,
		client:  &http.Client{Timeout: 10 * time.Second},
		users:   users,
		grps:    grps,
		syncs:   syncs,
	}
}

// Sync 全量同步用户 + 组织
func (c *IdentityConnector) Sync(ctx context.Context) error {
	job := &model.SyncJob{Type: model.SyncIdentity, Status: 1}
	now := time.Now()
	job.StartedAt = &now
	c.syncs.CreateJob(job)

	// 组织
	var orgs []IdentityOrg
	if err := c.getJSON(ctx, "/scim/v2/Organizations", &orgs); err != nil {
		c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return err
	}
	// 物化路径需按序（父先于子）；简单起见用 map 逐条构建
	pathByID := map[uint64]string{}
	// mock-identity 组织 id → 本地组织 id（父先于子，用于把父节点解析到本地 id，避免 mock id 与本地 id 不一致时重复建组织）
	localIDByMock := map[uint64]uint64{}
	for _, o := range orgs {
		p := fmt.Sprintf("/%d/", o.ID)
		if o.ParentID != nil {
			if pp, ok := pathByID[*o.ParentID]; ok {
				p = pp + fmt.Sprintf("%d/", o.ID)
			}
		}
		pathByID[o.ID] = p
		var localParentID *uint64
		if o.ParentID != nil {
			if lid, ok := localIDByMock[*o.ParentID]; ok {
				localParentID = &lid
			}
		}
		if err := c.upsertOrg(&model.Group{
			Name:     o.Name,
			ParentID: localParentID,
			Type:     model.GroupTypeOrg,
			Path:     p,
			Source:   model.SourceSync,
		}); err != nil {
			c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
			return err
		}
		if g, err := c.grps.FindOrgByNameParent(o.Name, localParentID, -1); err == nil {
			localIDByMock[o.ID] = g.ID
		}
	}

	// 用户
	var users []IdentityUser
	if err := c.getJSON(ctx, "/scim/v2/Users", &users); err != nil {
		c.syncs.FinishJob(job.ID, 0, map[string]any{"error": err.Error()})
		return err
	}
	created := 0
	for _, u := range users {
		existing, err := c.users.ByUsername(u.Username)
		if err != nil { // 不存在则创建（source=identity 只读）
			hash, _ := auth.HashPassword("identity-default-pw")
			if err := c.users.Create(&model.User{
				Username:     u.Username,
				DisplayName:  u.DisplayName,
				Email:        u.Email,
				PasswordHash: hash,
				Status:       u.Status,
				Attributes:   u.Attributes,
				Source:       model.SourceSync,
			}); err == nil {
				created++
			}
		} else {
			// 增量更新显示名/状态（JML：离职=停用）
			existing.DisplayName = u.DisplayName
			existing.Email = u.Email
			existing.Status = u.Status
			existing.Attributes = u.Attributes
			c.users.Update(existing)
		}
	}
	c.syncs.FinishJob(job.ID, 2, map[string]any{"users": len(users), "created": created, "orgs": len(orgs)})
	return nil
}

func (c *IdentityConnector) upsertOrg(g *model.Group) error {
	// 幂等：同名+同父视为同一节点（复用本地已建组织节点，避免重复组织树）
	// source<=0 = 不限来源，身份源组织收敛到 seed 已建的本地树
	// 注意：不覆盖已有 path（本地组织树以 seed 为准，mock-identity 的 id 与本地 id 不一致）
	if _, err := c.grps.FindOrgByNameParent(g.Name, g.ParentID, -1); err == nil {
		return nil
	}
	return c.grps.Create(g)
}

func (c *IdentityConnector) getJSON(ctx context.Context, path string, out any) error {
	url := c.baseURL + path
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("identity %s -> %d", path, resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, out)
}
