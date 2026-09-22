package api

import (
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// listTickets 审批中心统一工单视图（Phase 前端改造，D9：内部 mock 聚合，暂不真实接入透传）
// 聚合五类：权限申请（AccessRequest 1/2）、接入申请（RequestOnboard=3）、上架/下架（CapabilityPublishTask）、授权回收（RevokeRequest）、定制需求（RequestCustom=5，A8 非目录请求）
// 查询参数：type=apply|onboard|publish|revoke|custom|all（默认 all）；role=applicant|approver（默认 applicant）
func (d *Deps) listTickets(c *gin.Context) {
	tp := c.DefaultQuery("type", "all")
	role := c.DefaultQuery("role", "applicant")
	uid := d.currentUserID(c)

	type ticket struct {
		ID          uint64 `json:"id"`
		Type        string `json:"type"` // apply | onboard | publish | revoke
		Title       string `json:"title"`
		Sub         string `json:"sub"`
		TicketNo    string `json:"ticket_no"`
		Status      string `json:"status"`
		Requester   string `json:"requester"`
		GranteeType string `json:"grantee_type,omitempty"` // user | org | group | app
		GranteeName string `json:"grantee_name,omitempty"` // 授权主体名称
		CreatedAt   string `json:"created_at"`
		Approvers   int    `json:"approvers"`
		Route       string `json:"route"`
		Risk        string `json:"risk"`
	}
	items := make([]ticket, 0, 32)

	// 权限申请 + 接入申请
	if tp == "all" || tp == "apply" || tp == "onboard" {
		var reqs []model.AccessRequest
		q := d.DB
		if tp != "all" {
			if tp == "onboard" {
				q = q.Where("request_type = ?", model.RequestOnboard)
			} else if tp == "custom" {
				q = q.Where("request_type = ?", model.RequestCustom) // A8 定制需求独立 tab
			} else {
				// 权限申请 tab：不混入接入申请与定制需求（各有专属 tab）
				q = q.Where("request_type NOT IN ?", []int16{model.RequestOnboard, model.RequestCustom})
			}
		}
		if role == "approver" {
			q = q.Where("status = ?", model.ReqPending)
		} else {
			q = q.Where("applicant_id = ?", uid)
		}
		q.Order("id desc").Limit(100).Find(&reqs)
		// 待我审批：仅保留审批链包含当前用户（与侧栏红点/工作台待办口径一致）
		if role == "approver" {
			var filtered []model.AccessRequest
			for _, r := range reqs {
				app, err := d.Apps.ByID(r.AppID)
				if err != nil {
					continue
				}
				chain := d.buildApprovalChain(&r, app, r.ApplicantID)
				if d.inChain(uid, chain) {
					filtered = append(filtered, r)
				}
			}
			reqs = filtered
		}
		for _, r := range reqs {
			t := ticket{
				ID:          r.ID,
				Type:        "apply",
				Title:       "权限申请",
				Sub:         reasonOf(r),
				TicketNo:    "REQ-" + pad4(r.ID),
				Status:      reqStatusLabel(r.Status),
				Requester:   granteeDisplayName(r),
				GranteeType: r.GranteeType,
				GranteeName: r.GranteeName,
				CreatedAt:   r.CreatedAt.Format("2006-01-02 15:04"),
				Route:       "/requests/" + strconv.FormatUint(r.ID, 10),
				Risk:        riskLabel(r.RiskLevel),
			}
			if r.RequestType == model.RequestOnboard {
				t.Type = "onboard"
				t.Title = "接入申请"
			}
			if r.RequestType == model.RequestCustom {
				t.Type = "custom"
				t.Title = "定制需求"
			}
			if u, err := d.Users.ByID(r.ApplicantID); err == nil {
				t.Requester = u.DisplayName
			}
			items = append(items, t)
		}
	}

	// 上架 / 下架
	if tp == "all" || tp == "publish" {
		var tasks []model.CapabilityPublishTask
		q := d.DB.Order("id desc").Limit(30)
		if role == "approver" {
			q = q.Where("status = ?", 1) // 待处理（已发起），不混入已完成
		} else {
			q = q.Where("requester_id = ?", uid)
		}
		q.Find(&tasks)
		for _, tsk := range tasks {
			title := "预设上架"
			if tsk.Action == "offline" {
				title = "预设下架"
			}
			items = append(items, ticket{
				ID: tsk.ID, Type: "publish", Title: title,
				Sub:       "能力包 #" + strconv.FormatUint(tsk.CapabilityID, 10),
				TicketNo:  tsk.TicketNo,
				Status:    map[int16]string{1: "已发起", 2: "已完成"}[tsk.Status],
				CreatedAt: tsk.CreatedAt.Format("2006-01-02 15:04"),
				Route:     "",
			})
		}
	}

	// 授权回收
	if tp == "all" || tp == "revoke" {
		var revs []model.RevokeRequest
		q := d.DB.Order("id desc").Limit(30)
		if role == "approver" {
			q = q.Where("status = ?", model.RevokePending)
		} else {
			q = q.Where("requester_id = ?", uid)
		}
		q.Find(&revs)
		for _, r := range revs {
			items = append(items, ticket{
				ID: r.ID, Type: "revoke", Title: "授权回收",
				Sub:       "策略 #" + strconv.FormatUint(r.PolicyID, 10),
				TicketNo:  "REV-" + pad4(r.ID),
				Status:    map[int16]string{1: "待审批", 2: "已通过", 3: "已驳回"}[r.Status],
				CreatedAt: r.CreatedAt.Format("2006-01-02 15:04"),
				Route:     "",
			})
		}
	}

	c.JSON(200, gin.H{"items": items})
}

func reasonOf(r model.AccessRequest) string {
	if r.Reason != "" {
		return r.Reason
	}
	if p, ok := r.Content["preset_id"].(string); ok {
		return "预设: " + p
	}
	return "权限申请"
}

func pad4(id uint64) string {
	s := strconv.FormatUint(id, 10)
	for len(s) < 4 {
		s = "0" + s
	}
	return s
}

func reqStatusLabel(s int16) string {
	return map[int16]string{0: "草稿", 1: "待审批", 2: "已通过", 3: "已拒绝", 4: "已回收"}[s]
}

// granteeDisplayName 解析授权主体显示名（优先 GranteeName，兜底类型标签）
func granteeDisplayName(r model.AccessRequest) string {
	if r.GranteeName != "" {
		return r.GranteeName
	}
	switch r.ApplicantSubjectType {
	case model.ReqSubjectGroup:
		return "组织/组"
	case model.ReqSubjectApp:
		return "下游应用"
	default:
		return "个人"
	}
}
