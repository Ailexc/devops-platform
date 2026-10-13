package api

import (
	"context"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
)

// actionContract 从权限点 ID 列表生成接口契约（method/path/name + 请求响应示例）
// 基于授权实际包含的权限点，不依赖申请单预设（更通用）
func (d *Deps) actionContract(actionIDs []uint64) []map[string]any {
	if len(actionIDs) == 0 {
		return nil
	}
	acts, err := d.Access.ActionsByIDs(actionIDs)
	if err != nil {
		return nil
	}
	ops := []map[string]any{}
	for _, act := range acts {
		ops = append(ops, map[string]any{
			"action": act.Code, "method": act.Method, "path": act.Path,
			"name": act.Name,
			"req_example":  act.ReqExample,
			"resp_example": act.RespExample,
		})
	}
	return ops
}

// upstreamInterfaces 从接入/授权申请单解析接口契约（基于能力包预设 action_codes）
func (d *Deps) upstreamInterfaces(req *model.AccessRequest) []map[string]any {
	if req == nil {
		return nil
	}
	cid, _ := req.Content["capability_id"].(float64)
	pid, _ := req.Content["preset_id"].(string)
	if cid == 0 || pid == "" {
		return nil
	}
	cap, err := d.Caps.ByID(uint64(cid))
	if err != nil {
		return nil
	}
	p := d.findPreset(cap.Presets, pid)
	if p == nil {
		return nil
	}
	ops := []map[string]any{}
	if v, ok := p["action_codes"].([]any); ok {
		for _, x := range v {
			code, _ := x.(string)
			if code == "" {
				continue
			}
			act, err := d.Access.ActionByCode(cap.AppID, code)
			if err != nil {
				continue
			}
			ops = append(ops, map[string]any{
				"action": act.Code, "method": act.Method, "path": act.Path,
				"name": act.Name,
				"req_example":  act.ReqExample,
				"resp_example": act.RespExample,
			})
		}
	}
	return ops
}

// loadRequestByID 查申请单（供接口契约展示）
func (d *Deps) loadRequestByID(id uint64) *model.AccessRequest {
	if id == 0 {
		return nil
	}
	var r model.AccessRequest
	if err := d.DB.First(&r, id).Error; err != nil {
		return nil
	}
	return &r
}

// upstreamModels 对方应用提供的数据模型（资源同步投影按 app_id 归属过滤；AppID=0 的旧数据视为全局）
func (d *Deps) upstreamModels(appID uint64) []gin.H {
	ms, err := d.Res.Models()
	if err != nil {
		return nil
	}
	out := []gin.H{}
	for _, m := range ms {
		if m.AppID != 0 && m.AppID != appID {
			continue
		}
		out = append(out, gin.H{
			"id": m.ID, "code": m.Code, "name": m.Name,
			"attributes_schema": m.AttributesSchema,
		})
	}
	return out
}

// listAccessors 谁访问了我的应用（FR-7 资源方视角）
// type=app|user|group|org 过滤；默认全部
func (d *Deps) listAccessors(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	if _, err := d.Apps.ByID(appID); err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	ftype := c.Query("type")

	var ps []model.Policy
	d.DB.Where("app_id = ? AND status = ? AND effect = ?", appID, model.PolicyActive, model.EffectAllow).
		Order("id").Find(&ps)

	// 按主体聚合
	type accessor struct {
		SubjectType int16   `json:"subject_type"`
		SubjectID   uint64  `json:"subject_id"`
		Name        string  `json:"name"`
		Grants      []gin.H `json:"grants"`
		Sources     []int16 `json:"sources"`
	}
	seen := map[string]*accessor{}
	order := []string{}
	for _, p := range ps {
		st := p.SubjectType
		// type 过滤
		switch ftype {
		case "app":
			if st != model.SubjectService {
				continue
			}
		case "user":
			if st != model.SubjectUser {
				continue
			}
		case "group", "org":
			if st != model.SubjectGroup {
				continue
			}
		}
		key := strconv.FormatInt(int64(st), 10) + ":" + strconv.FormatUint(p.SubjectID, 10)
		a, ok := seen[key]
		if !ok {
			name := d.subjectName(st, p.SubjectID)
			a = &accessor{SubjectType: st, SubjectID: p.SubjectID, Name: name}
			seen[key] = a
			order = append(order, key)
		}
		acts, _ := d.Access.ActionsByIDs(p.ActionIDs)
		gr := gin.H{
			"id": p.ID, "name": p.Name, "actions": acts,
			"source": p.Source, "created_at": p.CreatedAt,
			"expires_at": p.ExpiresAt, "status": p.Status,
			"request_id": p.RequestID,
		}
		a.Grants = append(a.Grants, gr)
		if !containsInt(a.Sources, p.Source) {
			a.Sources = append(a.Sources, p.Source)
		}
	}
	var items []gin.H
	for _, key := range order {
		a := seen[key]
		items = append(items, gin.H{
			"subject_type": a.SubjectType,
			"subject_id":   a.SubjectID,
			"name":         a.Name,
			"grants_count": len(a.Grants),
			"sources":      a.Sources,
		})
	}
	c.JSON(200, gin.H{"items": items})
}

// accessorGrants 访问者授权明细（该主体在本应用的全部策略）
func (d *Deps) accessorGrants(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	sid, _ := strconv.ParseUint(c.Param("sid"), 10, 64)
	var ps []model.Policy
	d.DB.Where("app_id = ? AND subject_id = ? AND status = ?",
		appID, sid, model.PolicyActive).Order("id").Find(&ps)
	c.JSON(200, gin.H{"items": d.decoratePolicies(ps)})
}

// revokeGrant 发起授权回收（阶段 6：回收走审批）
// 仅应用 owner / 管理员可发起；审批链 = 应用其他 owner（SoD：申请人不审批自己的回收单）
// 单一 owner 时自动通过并立即执行
func (d *Deps) revokeGrant(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	p, err := d.Pol.ByID(id)
	if err != nil {
		c.JSON(404, gin.H{"error": "policy not found"})
		return
	}
	uid := d.currentUserID(c)
	// 可发起回收：应用 owner（管理视角）或授权作用到自己的 grantee（本人 / 所属组，退还视角）
	owner := d.isAppOwner(uid, p.AppID)
	grantee := false
	switch p.SubjectType {
	case model.SubjectUser:
		grantee = p.SubjectID == uid
	case model.SubjectGroup:
		groups, _ := d.Groups.ByUserID(uid)
		for _, gid := range d.allGroupIDsForUser(uid, groups) {
			if gid == p.SubjectID {
				grantee = true
				break
			}
		}
	}
	if !owner && !grantee {
		c.JSON(403, gin.H{"error": "only app owner or the grantee can request revocation"})
		return
	}
	var req struct {
		Reason string `json:"reason"`
	}
	c.ShouldBindJSON(&req)
	rr := &model.RevokeRequest{
		PolicyID:    id,
		AppID:       p.AppID,
		RequesterID: uid,
		Reason:      req.Reason,
		Status:      model.RevokePending,
	}
	if err := d.DB.Create(rr).Error; err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	// 审批链：应用其他 owner
	approver := d.otherOwner(p.AppID, uid)
	if approver == 0 {
		// 无其他 owner → 自动通过并执行
		if err := d.executeRevoke(rr, uid, "auto (sole owner)"); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
		d.audit(c, "grant.revoke.auto", "policy", strconv.FormatUint(id, 10),
			gin.H{"revoke_request_id": rr.ID})
		c.JSON(200, gin.H{"id": rr.ID, "status": "revoked", "auto": true})
		return
	}
	d.audit(c, "grant.revoke.request", "policy", strconv.FormatUint(id, 10),
		gin.H{"revoke_request_id": rr.ID, "approver": approver, "reason": req.Reason})
	c.JSON(201, gin.H{"id": rr.ID, "status": "pending", "approver": approver})
}

// listRevokeRequests 回收申请列表：?role=approver 待我审批；默认我发起的
func (d *Deps) listRevokeRequests(c *gin.Context) {
	uid := d.currentUserID(c)
	var rs []model.RevokeRequest
	if c.Query("role") == "approver" {
		d.DB.Where("status = ?", model.RevokePending).Order("id desc").Find(&rs)
		out := make([]gin.H, 0)
		for _, r := range rs {
			// 审批人 = 该应用 owner 且不是申请人（SoD）
			if d.isAppOwner(uid, r.AppID) && uid != r.RequesterID {
				out = append(out, d.revokeView(&r))
			}
		}
		c.JSON(200, gin.H{"items": out})
		return
	}
	d.DB.Where("requester_id = ?", uid).Order("id desc").Find(&rs)
	out := make([]gin.H, 0, len(rs))
	for i := range rs {
		out = append(out, d.revokeView(&rs[i]))
	}
	c.JSON(200, gin.H{"items": out})
}

// approveRevokeRequest 审批回收申请（SoD：申请人不能审批自己的回收单）
func (d *Deps) approveRevokeRequest(c *gin.Context) {
	id, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	var req struct {
		Action  int16  `json:"action"` // 1=通过 2=驳回
		Comment string `json:"comment"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad request"})
		return
	}
	var rr model.RevokeRequest
	if err := d.DB.First(&rr, id).Error; err != nil {
		c.JSON(404, gin.H{"error": "revoke request not found"})
		return
	}
	if rr.Status != model.RevokePending {
		c.JSON(400, gin.H{"error": "revoke request not pending"})
		return
	}
	uid := d.currentUserID(c)
	if uid == rr.RequesterID {
		c.JSON(403, gin.H{"error": "SoD: requester cannot approve own revoke request"})
		return
	}
	// 审批人必须是应用 owner
	if !d.isAppOwner(uid, rr.AppID) {
		c.JSON(403, gin.H{"error": "only app owner can approve revocation"})
		return
	}
	rr.ApproverID = uid
	rr.Comment = req.Comment
	if req.Action == model.ApproveNo {
		rr.Status = model.RevokeRejected
		d.DB.Save(&rr)
		d.audit(c, "grant.revoke.reject", "revoke_request", strconv.FormatUint(id, 10),
			gin.H{"comment": req.Comment})
		c.JSON(200, gin.H{"status": "rejected"})
		return
	}
	if err := d.executeRevoke(&rr, uid, req.Comment); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	d.audit(c, "grant.revoke.approve", "revoke_request", strconv.FormatUint(id, 10),
		gin.H{"comment": req.Comment, "approver": uid})
	c.JSON(200, gin.H{"status": "revoked"})
}

// executeRevoke 执行回收：停用策略 + 撤销 OpenFGA 关系 + 缓存/bundle 失效
func (d *Deps) executeRevoke(rr *model.RevokeRequest, approver uint64, comment string) error {
	p, err := d.Pol.ByID(rr.PolicyID)
	if err != nil {
		return err
	}
	if p.Status == model.PolicyDisabled {
		rr.Status = model.RevokeApproved
		rr.ApproverID = approver
		rr.Comment = comment
		now := timeNow()
		rr.ApprovedAt = &now
		d.DB.Save(rr)
		return nil // 已回收，幂等
	}
	p.Status = model.PolicyDisabled
	if err := d.Pol.Update(p); err != nil {
		return err
	}
	// （1.5 T3）集合式判定=点查行比对（CheckRow），不再物化/撤销 OpenFGA 元组
	d.bumpAllCaches(nil)
	d.BundleMgr.Publish(context.Background(), p.AppID)
	rr.Status = model.RevokeApproved
	rr.ApproverID = approver
	rr.Comment = comment
	now := timeNow()
	rr.ApprovedAt = &now
	return d.DB.Save(rr).Error
}

// revokeView 回收申请展示视图
func (d *Deps) revokeView(r *model.RevokeRequest) gin.H {
	v := gin.H{
		"id": r.ID, "policy_id": r.PolicyID, "app_id": r.AppID,
		"requester_id": r.RequesterID, "reason": r.Reason,
		"status": r.Status, "approver_id": r.ApproverID,
		"comment": r.Comment, "approved_at": r.ApprovedAt,
		"created_at": r.CreatedAt,
	}
	if req, err := d.Users.ByID(r.RequesterID); err == nil {
		v["requester_name"] = req.DisplayName
	}
	if r.ApproverID > 0 {
		if ap, err := d.Users.ByID(r.ApproverID); err == nil {
			v["approver_name"] = ap.DisplayName
		}
	}
	if p, err := d.Pol.ByID(r.PolicyID); err == nil {
		v["policy_name"] = p.Name
		v["subject_type"] = p.SubjectType
		v["subject_id"] = p.SubjectID
		acts, _ := d.Access.ActionsByIDs(p.ActionIDs)
		v["actions"] = acts
	}
	return v
}

// otherOwner 返回应用除 uid 外的其他 owner（审批人）；无则返回 0
func (d *Deps) otherOwner(appID, uid uint64) uint64 {
	var owners []model.AppOwner
	d.DB.Where("app_id = ?", appID).Find(&owners)
	for _, o := range owners {
		if o.UserID != uid {
			return o.UserID
		}
	}
	return 0
}

// listUpstreams 我的应用申请了谁（FR-7 下游视角）：本应用 client（service）获得的对外授权
func (d *Deps) listUpstreams(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	if _, err := d.Apps.ByID(appID); err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	// 本应用的 client IDs
	var clis []model.Client
	d.DB.Where("app_id = ?", appID).Find(&clis)
	clientIDs := make([]uint64, 0, len(clis))
	for _, cl := range clis {
		clientIDs = append(clientIDs, cl.ID)
	}
	var items []gin.H
	covered := map[uint64]bool{} // 已通过上游（策略段已展示，申请单段跳过避免重复）
	if len(clientIDs) > 0 {
		var ps []model.Policy
		d.DB.Where("subject_type = ? AND subject_id IN ? AND status = ?",
			model.SubjectService, clientIDs, model.PolicyActive).Find(&ps)
		// 按上游应用聚合：合并所有 policy 的 action_ids（去重），并取第一个有效 request_id/subjectID 留痕
		type agg struct {
			actionIDs []uint64
			reqID     uint64
			subjectID uint64
		}
		byApp := map[uint64]*agg{}
		appOrder := []uint64{}
		seenAction := map[uint64]bool{}
		for _, p := range ps {
			a, ok := byApp[p.AppID]
			if !ok {
				a = &agg{}
				byApp[p.AppID] = a
				appOrder = append(appOrder, p.AppID)
			}
			if a.reqID == 0 && p.RequestID != nil {
				a.reqID = *p.RequestID
			}
			if a.subjectID == 0 {
				a.subjectID = p.SubjectID
			}
			for _, id := range p.ActionIDs {
				if id > 0 && !seenAction[id] {
					seenAction[id] = true
					a.actionIDs = append(a.actionIDs, id)
				}
			}
		}
		for _, upAppID := range appOrder {
			a := byApp[upAppID]
			upName, upCode, upDocURL := "", "", ""
			if up, err := d.Apps.ByID(upAppID); err == nil {
				upName, upCode, upDocURL = up.Name, up.Code, up.DocURL
			}
			// 查找对应的 client_id
			clientID := ""
			for _, cl := range clis {
				if cl.ID == a.subjectID {
					clientID = cl.ClientID
					break
				}
			}
			ifs := d.actionContract(a.actionIDs)
			if len(ifs) == 0 {
				ifs = d.upstreamInterfaces(d.loadRequestByID(a.reqID))
			}
			items = append(items, gin.H{
				"upstream_app_id": upAppID, "upstream_name": upName, "upstream_code": upCode,
				"source": model.SourceViaRequest, "request_id": a.reqID,
				"client_id": clientID, "credential_status": "active",
				"interfaces": ifs,
				"doc_url":    upDocURL,
				"models":     d.upstreamModels(upAppID),
			})
			covered[upAppID] = true
		}
	}
	// 加上本应用作为申请主体的申请单（app_request 方向；跳过已被策略段覆盖的已通过上游，避免重复）
	var reqs []model.AccessRequest
	d.DB.Where("applicant_subject_type = ? AND applicant_subject_id = ?", model.ReqSubjectApp, appID).
		Find(&reqs)
	for _, r := range reqs {
		if covered[r.AppID] {
			continue
		}
		upName, upCode, upDocURL := "", "", ""
		if up, err := d.Apps.ByID(r.AppID); err == nil {
			upName, upCode, upDocURL = up.Name, up.Code, up.DocURL
		}
		// 查找对应的 client_id（如果有）
		clientID := ""
		credentialStatus := "pending"
		if r.Status == model.ReqApproved {
			credentialStatus = "active"
			// 查找该应用下的 client
			var appClis []model.Client
			d.DB.Where("app_id = ?", appID).Find(&appClis)
			if len(appClis) > 0 {
				clientID = appClis[0].ClientID
			}
		} else if r.Status == model.ReqRejected {
			credentialStatus = "rejected"
		}
		items = append(items, gin.H{
			"upstream_app_id": r.AppID, "upstream_name": upName, "upstream_code": upCode,
			"source": model.SourceAppRequest, "request_id": r.ID,
			"status": r.Status, "client_id": clientID,
			"credential_status": credentialStatus,
			"interfaces": d.upstreamInterfaces(&r),
			"doc_url":    upDocURL,
			"models":     d.upstreamModels(r.AppID),
		})
	}
	c.JSON(200, gin.H{"items": items})
}

// ---- 辅助 ----

func (d *Deps) subjectName(st int16, sid uint64) string {
	switch st {
	case model.SubjectUser:
		if u, err := d.Users.ByID(sid); err == nil {
			return u.DisplayName
		}
	case model.SubjectGroup:
		if g, err := d.Groups.ByID(sid); err == nil {
			return g.Name
		}
	case model.SubjectService:
		if cl, err := d.Apps.ClientByRowID(sid); err == nil {
			return cl.ClientID
		}
	}
	return "subject-" + strconv.FormatUint(sid, 10)
}

func containsInt(list []int16, v int16) bool {
	for _, x := range list {
		if x == v {
			return true
		}
	}
	return false
}
