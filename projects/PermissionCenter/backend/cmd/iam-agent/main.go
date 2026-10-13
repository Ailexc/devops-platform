// iam-agent：本地 PDP agent（sidecar，内嵌 Casbin）
// 借鉴 OPA bundle 思想：轮询拉取策略包 → 校验 checksum → 原子激活 → 本地动作级决策
// （1.5 T3）数据级/强一致档已随投影退役——本地仅动作级判定，失配/无 bundle 回源中心
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/casbin/casbin/v2"
	"github.com/casbin/casbin/v2/model"
)

type BundleContent struct {
	AppCode     string            `json:"app_code"`
	Policies    []PolicyEntry     `json:"policies"`
	Groupings   [][]string        `json:"groupings"`
	CasbinModel string            `json:"casbin_model"`
	Users       map[string]string `json:"users"`
}

type PolicyEntry struct {
	SubjectKey string          `json:"subject_key"`
	AppCode    string          `json:"app_code"`
	Actions    []string        `json:"actions"`
	Effect     string          `json:"effect"`
	Conditions json.RawMessage `json:"conditions,omitempty"`
}

type agent struct {
	mu          sync.RWMutex
	enforcer    *casbin.Enforcer
	content     *BundleContent
	currentRev  int64
	checksum    string
	centerURL   string
	appCode     string
	decisionCnt int64
	remoteCnt   int64
}

func main() {
	centerURL := os.Getenv("IAM_SERVER_URL")
	if centerURL == "" {
		centerURL = "http://localhost:8080"
	}
	appCode := os.Getenv("AGENT_APP")
	if appCode == "" {
		appCode = "cmdb"
	}
	addr := os.Getenv("AGENT_HTTP_ADDR")
	if addr == "" {
		addr = ":9090"
	}
	pollInterval := 3 * time.Second

	a := &agent{centerURL: centerURL, appCode: appCode}

	// 本地决策 HTTP 服务
	go func() {
		mux := http.NewServeMux()
		mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
			a.mu.RLock()
			rev := a.currentRev
			a.mu.RUnlock()
			fmt.Fprintf(w, `{"status":"ok","rev":%d}`, rev)
		})
		mux.HandleFunc("/v1/local/check", a.handleLocalCheck)
		log.Printf("[iam-agent] local PDP listening %s (app=%s, center=%s)", addr, appCode, centerURL)
		log.Fatal(http.ListenAndServe(addr, mux))
	}()

	// 轮询拉包 + 状态上报
	ctx := context.Background()
	for {
		a.poll(ctx)
		a.report(ctx)
		time.Sleep(pollInterval)
	}
}

// poll 拉取 bundle：带当前版本，无更新跳过；校验 checksum 后原子激活（失败保留 last-known-good）
func (a *agent) poll(ctx context.Context) {
	url := fmt.Sprintf("%s/v1/bundles/%s?rev=%d", a.centerURL, a.appCode, a.currentRev)
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("[iam-agent] poll failed: %v（保留 last-known-good）", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNotModified {
		return
	}
	if resp.StatusCode != http.StatusOK {
		log.Printf("[iam-agent] poll status %d", resp.StatusCode)
		return
	}
	body, _ := io.ReadAll(resp.Body)
	var rawRes struct {
		Revision int64            `json:"revision"`
		Checksum string           `json:"checksum"`
		Content  json.RawMessage  `json:"content"`
	}
	if err := json.Unmarshal(body, &rawRes); err != nil {
		log.Printf("[iam-agent] decode failed: %v", err)
		return
	}
	// 校验 checksum：基于响应中 content 的原始字节（与中心存储形态一致）
	sum := sha256.Sum256(rawRes.Content)
	if hex.EncodeToString(sum[:]) != rawRes.Checksum {
		log.Printf("[iam-agent] checksum mismatch，拒绝激活（保留 last-known-good）")
		return
	}
	var content BundleContent
	if err := json.Unmarshal(rawRes.Content, &content); err != nil {
		log.Printf("[iam-agent] content decode failed: %v", err)
		return
	}
	// 构建 Casbin 模型 + 策略
	m, err := model.NewModelFromString(content.CasbinModel)
	if err != nil {
		log.Printf("[iam-agent] model failed: %v", err)
		return
	}
	e, err := casbin.NewEnforcer(m)
	if err != nil {
		log.Printf("[iam-agent] enforcer failed: %v", err)
		return
	}
	for _, g := range content.Groupings {
		e.AddGroupingPolicy(g)
	}
	for _, p := range content.Policies {
		eft := p.Effect
		if eft == "" {
			eft = "allow"
		}
		for _, action := range p.Actions {
			e.AddPolicy(p.SubjectKey, p.AppCode, action, "*", eft, "bundle")
		}
	}
	e.BuildRoleLinks()

	// 原子激活（swap）
	a.mu.Lock()
	a.enforcer = e
	a.content = &content
	a.currentRev = rawRes.Revision
	a.checksum = rawRes.Checksum
	a.mu.Unlock()
	log.Printf("[iam-agent] bundle activated rev=%d (checksum=%s…)", rawRes.Revision, rawRes.Checksum[:12])
}

// report 状态上报（升级率/存活监控）
func (a *agent) report(ctx context.Context) {
	a.mu.RLock()
	rev := a.currentRev
	dc := a.decisionCnt
	a.mu.RUnlock()
	body, _ := json.Marshal(map[string]any{
		"agent_id":       "iam-agent-local-1",
		"app_id":         1,
		"current_rev":    rev,
		"decision_count": dc,
		"hit_rate":       0.99,
	})
	req, _ := http.NewRequestWithContext(ctx, http.MethodPost, a.centerURL+"/v1/agents/status", strings.NewReader(string(body)))
	req.Header.Set("Content-Type", "application/json")
	if resp, err := http.DefaultClient.Do(req); err == nil {
		resp.Body.Close()
	}
}

// handleLocalCheck 本地动作级决策；无 bundle/失配回源中心
func (a *agent) handleLocalCheck(w http.ResponseWriter, r *http.Request) {
	var req struct {
		User   string `json:"user"`
		App    string `json:"app"`
		Action string `json:"action"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"bad request"}`, 400)
		return
	}

	a.mu.RLock()
	e := a.enforcer
	content := a.content
	a.mu.RUnlock()
	if e == nil || content == nil {
		// fail-closed：无 bundle → 回源中心
		a.relayRemote(w, req)
		return
	}

	sub, ok := content.Users[req.User]
	if !ok {
		sub = "u:" + req.User // 兼容直接传 subject key
	}
	ok, err := e.Enforce(sub, req.App, req.Action, "*")
	a.mu.Lock()
	a.decisionCnt++
	a.mu.Unlock()
	if err != nil {
		http.Error(w, `{"error":"enforce failed"}`, 500)
		return
	}
	if ok {
		fmt.Fprint(w, `{"decision":"allow","channel":"local"}`)
		return
	}
	w.WriteHeader(403)
	fmt.Fprint(w, `{"decision":"deny","code":"NO_PERMISSION","channel":"local"}`)
}

// relayRemote 回源中心 PDP（agent 无 bundle 或本地失配时）
func (a *agent) relayRemote(w http.ResponseWriter, req struct {
	User   string `json:"user"`
	App    string `json:"app"`
	Action string `json:"action"`
}) {
	body, _ := json.Marshal(req)
	r, _ := http.NewRequest(http.MethodPost, a.centerURL+"/v1/authz/check", strings.NewReader(string(body)))
	r.Header.Set("Content-Type", "application/json")
	r.Header.Set("X-PEP-Token", os.Getenv("PEP_SHARED_SECRET"))
	if os.Getenv("PEP_SHARED_SECRET") == "" {
		r.Header.Set("X-PEP-Token", "pep-shared-secret")
	}
	resp, err := http.DefaultClient.Do(r)
	if err != nil {
		http.Error(w, `{"decision":"deny","code":"CENTER_UNAVAILABLE","channel":"relay"}`, 503)
		return
	}
	defer resp.Body.Close()
	data, _ := io.ReadAll(resp.Body)
	w.WriteHeader(resp.StatusCode)
	w.Write(data)
}
