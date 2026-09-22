package sync

// PatrolService 数据契约巡检 + 深对账（清单 A4/A5b——2.3.1 确认制状态机的执行体）
//
// 分工（拍板红线的落点）：判定侧（A6）只读契约时钟做三态门槛；本服务负责"让时钟往前走"——
//   指纹比对/增量同步刷新时钟；失败历史写 patrol_log（观测与告警分级进，**判定不读本表**）。
//
// 通道对应：指纹比对+增量拉 = 指纹巡检通道（分钟级）；ReconcileOnce = 深对账通道（天级兜底）。

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

type PatrolService struct {
	contracts *store.ContractRepo
	res       *store.ResourceRepo
	cmdb      *CMDBConnector
	syncs     *store.SyncRepo
	overlap   time.Duration                                                 // 增量水位回拨重叠窗口（≈巡检周期 10%，兜两侧时钟偏差）
	purge     func(ctx context.Context, modelCode, externalID string) error // OpenFGA 关系级联清理（A5a 原语，深对账兜底复用）
	lastState map[string]string                                             // 域上次巡检状态（内存；recovery 跃迁检测用——单实例足够）
}

func NewPatrolService(contracts *store.ContractRepo, res *store.ResourceRepo, cmdb *CMDBConnector,
	syncs *store.SyncRepo, overlap time.Duration,
	purge func(ctx context.Context, modelCode, externalID string) error) *PatrolService {
	if overlap < time.Second {
		overlap = time.Second
	}
	return &PatrolService{
		contracts: contracts, res: res, cmdb: cmdb, syncs: syncs,
		overlap: overlap, purge: purge, lastState: map[string]string{},
	}
}

// PatrolOnce 巡检一轮（每启用契约的数据域）：
//
//	上游指纹 → 与本地集合指纹比对 → 一致：确认制时钟刷新 + 水位=now（确认"无新数据"）
//	                                → 失配：增量同步（成功=时钟刷新+水位=queryStart；失败=时钟不动）
//	          → 不可达/本地异常：时钟不动
//
// 三路均写 patrol_log 失败/成功历史；状态跃迁回 Fresh 记 recovery 决策日志（2.3.1 裁定③自动自愈可观测）
func (s *PatrolService) PatrolOnce(ctx context.Context) {
	now := time.Now()
	cs, err := s.contracts.ListEnabled()
	if err != nil {
		log.Printf("[patrol] list contracts: %v", err)
		return
	}
	for i := range cs {
		dc := &cs[i]
		if _, err := s.res.ModelByCode(dc.ModelCode); err != nil {
			continue // 数据域尚无投影（如未接 mock 的资产域）→ 跳过，不误伤
		}
		ageBefore, _ := dc.Freshness(now)

		up, ferr := s.cmdb.FetchFingerprint(ctx, dc.ModelCode)
		if ferr != nil {
			s.logPatrol(dc, now, false, false, false, ageBefore)
			s.transition(dc, now, false)
			continue
		}
		localIDs, localTS, _, lerr := s.res.SetFingerprint(dc.ModelCode)
		if lerr != nil {
			s.logPatrol(dc, now, true, false, false, ageBefore)
			s.transition(dc, now, false)
			continue
		}
		if localIDs == up.HashIDs && localTS == up.HashUpdatedAt {
			// 确认制：指纹一致 = 确认"没有新数据" → 时钟刷新；无待拉变更 → 水位=now
			s.contracts.TouchFresh(dc.ID, now)
			s.contracts.UpdateWatermark(dc.ID, now)
			s.logPatrol(dc, now, true, true, true, 0)
			s.transition(dc, now, true)
			continue
		}
		// 失配 → 增量拉取；水位批末推进：SyncInstancesSince 返回 nil（=全部写成功）后才推
		_, _, _, queryStart, serr := s.cmdb.SyncInstancesSince(ctx, dc.ModelCode, dc.SyncWatermarkAt, s.overlap)
		if serr != nil {
			s.logPatrol(dc, now, true, true, false, ageBefore)
			s.transition(dc, now, false)
			continue
		}
		s.contracts.TouchFresh(dc.ID, now)
		s.contracts.UpdateWatermark(dc.ID, queryStart)
		s.logPatrol(dc, now, true, false, true, ageBefore)
		s.transition(dc, now, true)
	}
}

// transition 巡检状态跃迁记录 + recovery 事件（reason=recovery 可查，A6 验收项）
func (s *PatrolService) transition(dc *model.DataContract, now time.Time, healthy bool) {
	state := model.FreshStateFresh
	if !healthy {
		_, state = dc.Freshness(now) // 未刷新时钟：按当前年龄判态（expired/degraded 供跃迁比对）
	}
	prev := s.lastState[dc.ModelCode]
	s.lastState[dc.ModelCode] = state
	if healthy && prev != "" && prev != model.FreshStateFresh {
		s.syncs.CreateDecision(&model.DecisionLog{
			Action: "patrol.recovery", Resource: dc.ModelCode,
			Decision: int16(model.DecisionAllow), Reason: "recovery", Channel: model.ChannelRemote,
		})
		log.Printf("[patrol] recovery %s: %s -> fresh（同步落地/指纹确认，时钟恢复）", dc.ModelCode, prev)
	}
}

// logPatrol 写巡检失败历史（观测/告警分级进；判定只读状态机）
func (s *PatrolService) logPatrol(dc *model.DataContract, at time.Time, reachable, match, syncOK bool, age time.Duration) {
	s.contracts.CreatePatrolLog(&model.PatrolLog{
		Domain: dc.ModelCode, At: at, Reachable: reachable,
		FingerprintMatch: match, SyncOK: syncOK, FreshAgeSec: int(age.Seconds()),
	})
}

// ReconcileOnce 深对账（清单 A5b：低频全量兜底，"先取后比再写"）：
//   - 孤儿（本地有上游没有）→ 删投影 + 级联清 OpenFGA tuple（天级兜 A5a 漏网/静默删除——幽灵授权红线）
//   - 静默漂移（ts 相同但记录 fp 不同——L1/L2 集合指纹全盲区）→ 记录告警 + upsert 收敛
//   - 常规更新/新增 → upsert；按域产出 SyncJob(type=5) 结果可查
//
// 跳过规则：上游无此域（404）且本地为空 → 非 mock 承载域（如 ops 自有资源目录），静默跳过。
func (s *PatrolService) ReconcileOnce(ctx context.Context) map[string]any {
	summary := map[string]any{}
	models, err := s.res.Models()
	if err != nil {
		log.Printf("[reconcile] list models: %v", err)
		return summary
	}
	for _, m := range models {
		local, lerr := s.res.InstancesByModelAll(m.ID)
		if lerr != nil {
			summary[m.Code] = map[string]any{"error": lerr.Error()}
			continue
		}
		insts, ferr := s.cmdb.FetchAllInstances(ctx, m.Code)
		if ferr != nil {
			if len(local) == 0 {
				continue // 上游无此域 + 本地为空 → 非 mock 承载域，静默跳过
			}
			summary[m.Code] = map[string]any{"error": ferr.Error(), "local": len(local)}
			continue
		}
		job := &model.SyncJob{Type: model.SyncReconcile, Status: 1}
		now := time.Now()
		job.StartedAt = &now
		s.syncs.CreateJob(job)

		upExt := make(map[string]CMDBInstance, len(insts))
		for _, inst := range insts {
			upExt[fmt.Sprintf("%s-%d", m.Code, inst.ID)] = inst
		}
		var orphans, drift []string
		for _, row := range local {
			up, ok := upExt[row.ExternalID]
			if !ok {
				orphans = append(orphans, row.ExternalID)
				continue
			}
			// 静默漂移判定：上游时间戳相同（L1/L2 指纹盲）但记录级 fp 不同 → 内容被改
			upTS := parseUpstreamTS(up.UpdatedAt)
			if row.UpstreamUpdatedAt != nil && upTS != nil && row.UpstreamUpdatedAt.Equal(*upTS) {
				tmp := model.ResourceInstance{
					ModelID: m.ID, ExternalID: row.ExternalID,
					Name: up.Name, Attributes: up.Attributes, OwnerID: up.OwnerID,
				}
				if model.ComputeInstanceFP(&tmp) != row.FP {
					drift = append(drift, row.ExternalID)
				}
			}
		}
		// ① 孤儿双侧清理（PG 投影 + OpenFGA 关系——A5a 天级兜底）
		for _, ext := range orphans {
			if derr := s.res.DeleteInstanceByExternal(m.ID, ext); derr != nil {
				log.Printf("[reconcile] delete orphan %s: %v", ext, derr)
				continue
			}
			if s.purge != nil {
				if perr := s.purge(ctx, m.Code, ext); perr != nil {
					log.Printf("[reconcile] purge tuples %s: %v", ext, perr)
				}
			}
		}
		// ② 更新/新增/漂移收敛（upsert：fp 不同 → 写；单调守卫防乱序）
		written, skipped := 0, 0
		for _, up := range insts {
			ok, uerr := s.res.UpsertInstance(&model.ResourceInstance{
				ModelID:           m.ID,
				ExternalID:        fmt.Sprintf("%s-%d", m.Code, up.ID),
				Name:              up.Name,
				Attributes:        up.Attributes,
				OwnerID:           up.OwnerID,
				UpstreamUpdatedAt: parseUpstreamTS(up.UpdatedAt),
				SyncedAt:          &now,
			})
			if uerr != nil {
				log.Printf("[reconcile] upsert %s: %v", up.Name, uerr)
				continue
			}
			if ok {
				written++
			} else {
				skipped++
			}
		}
		detail := map[string]any{
			"orphans": orphans, "drift": drift, "written": written, "skipped": skipped,
		}
		s.syncs.FinishJob(job.ID, 2, detail)
		summary[m.Code] = detail
		if len(orphans) > 0 || len(drift) > 0 {
			log.Printf("[reconcile] %s orphans=%v drift=%v（孤儿已双侧清理；漂移=静默变更，L1/L2 盲区天级兜底）", m.Code, orphans, drift)
		}
	}
	return summary
}
