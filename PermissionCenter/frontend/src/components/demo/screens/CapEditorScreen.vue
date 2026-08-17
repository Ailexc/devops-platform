<template>
  <div class="mock-screen cap-editor-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">应用管理 / 小黄的监控服务 / <b>主机监控</b></div>
      <div class="mock-user">👤 小黄</div>
    </div>
    <div class="mock-content">
      <div class="editor-header">
        <h2 class="mock-title">📦 主机监控 · 能力编辑器</h2>
        <span class="status-tag draft">草稿</span>
      </div>

      <!-- 基础信息 -->
      <div class="section-card">
        <div class="section-label">基础信息</div>
        <div class="form-row"><span class="form-key">能力名称</span><span class="form-val">主机监控</span></div>
        <div class="form-row"><span class="form-key">描述</span><span class="form-val">主机列表查看与详情读取能力</span></div>
        <div class="form-row"><span class="form-key">数据模型</span><span class="form-val mono">host（主机）</span></div>
      </div>

      <!-- 接口绑定 -->
      <div class="section-card">
        <div class="section-label">🔌 绑定接口</div>
        <table class="api-table">
          <thead>
            <tr><th>接口 Code</th><th>方法</th><th>路径</th><th>操作</th><th>绑定</th></tr>
          </thead>
          <tbody>
            <tr class="row-on">
              <td><code>host:list</code></td>
              <td><span class="method get">GET</span></td>
              <td class="path">/api/v1/hosts</td>
              <td>列举主机</td>
              <td>✅</td>
            </tr>
            <tr class="row-on">
              <td><code>host:read</code></td>
              <td><span class="method get">GET</span></td>
              <td class="path">/api/v1/hosts/:id</td>
              <td>读取详情</td>
              <td>✅</td>
            </tr>
            <tr class="row-off">
              <td><code>host:create</code></td>
              <td><span class="method post">POST</span></td>
              <td class="path">/api/v1/hosts</td>
              <td>创建主机</td>
              <td>⬜</td>
            </tr>
            <tr class="row-off">
              <td><code>host:update</code></td>
              <td><span class="method put">PUT</span></td>
              <td class="path">/api/v1/hosts/:id</td>
              <td>更新主机</td>
              <td>⬜</td>
            </tr>
            <tr class="row-off">
              <td><code>host:delete</code></td>
              <td><span class="method del">DEL</span></td>
              <td class="path">/api/v1/hosts/:id</td>
              <td>删除主机</td>
              <td>⬜</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 数据范围控制 -->
      <div class="section-card scope-card">
        <div class="section-label">🔐 数据范围控制</div>
        <div class="scope-desc">为绑定接口配置数据级权限，申请者只能访问匹配范围内的数据实例</div>

        <div class="scope-grid">
          <div class="scope-dim">
            <div class="dim-header">
              <span class="dim-icon">🌍</span>
              <span class="dim-name">环境维度</span>
              <span class="dim-badge">单选</span>
            </div>
            <div class="dim-options">
              <span class="dim-opt active">🟢 prod</span>
              <span class="dim-opt">🟡 staging</span>
              <span class="dim-opt">🔵 dev</span>
            </div>
          </div>

          <div class="scope-dim">
            <div class="dim-header">
              <span class="dim-icon">📍</span>
              <span class="dim-name">地域维度</span>
              <span class="dim-badge">多选</span>
            </div>
            <div class="dim-options">
              <span class="dim-opt active">cn-north</span>
              <span class="dim-opt active">cn-south</span>
              <span class="dim-opt">ap-southeast</span>
            </div>
          </div>

          <div class="scope-dim">
            <div class="dim-header">
              <span class="dim-icon">🖥️</span>
              <span class="dim-name">实例维度</span>
              <span class="dim-badge">可选</span>
            </div>
            <div class="dim-options">
              <span class="dim-opt">web-01</span>
              <span class="dim-opt">web-02</span>
              <span class="dim-opt dim-disabled">db-01（不可选）</span>
            </div>
          </div>
        </div>

        <div class="scope-expr">
          <div class="expr-label">生成的 CEL 表达式（OpenFGA 数据策略）</div>
          <code class="expr-code">env == "prod" &amp;&amp; region in ["cn-north", "cn-south"]</code>
        </div>
      </div>

      <!-- 预设预览 -->
      <div class="section-card">
        <div class="section-label">🏷️ 权限预设（2 个）</div>
        <div class="preset-list">
          <div class="preset-item active">
            <div class="preset-head">
              <span class="preset-name">🔖 只读监控</span>
              <span class="preset-apis">2 个接口</span>
            </div>
            <div class="preset-detail">
              <span class="api-tag">host:list</span>
              <span class="api-tag">host:read</span>
              <span class="scope-tag">🔐 env=prod + cn-north/south</span>
            </div>
          </div>
          <div class="preset-item">
            <div class="preset-head">
              <span class="preset-name">🔖 完整监控</span>
              <span class="preset-apis">5 个接口</span>
            </div>
            <div class="preset-detail">
              <span class="api-tag">host:list</span>
              <span class="api-tag">host:read</span>
              <span class="api-tag">host:create</span>
              <span class="api-tag">host:update</span>
              <span class="api-tag">host:delete</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 16px 22px; overflow: auto; }
.editor-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.mock-title { font-size: 17px; font-weight: 700; color: var(--text); }
.status-tag { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px; }
.status-tag.draft { color: var(--warning); background: var(--warning-bg); }
.section-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.section-label { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.form-row { display: flex; align-items: center; padding: 3px 0; font-size: 12px; }
.form-key { color: var(--text-tertiary); width: 60px; flex-shrink: 0; }
.form-val { color: var(--text); font-weight: 500; }
.form-val.mono { font-family: var(--font-mono); font-size: 11px; background: var(--bg-tertiary); padding: 1px 6px; border-radius: 4px; }

/* API 表格 */
.api-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.api-table th { text-align: left; padding: 5px 6px; color: var(--text-tertiary); font-weight: 500; border-bottom: 1px solid var(--border); font-size: 10px; }
.api-table td { padding: 5px 6px; border-bottom: 1px solid var(--border); }
.api-table code { font-family: var(--font-mono); font-size: 11px; font-weight: 600; }
.row-on { background: var(--success-bg); }
.row-on td { color: var(--text); }
.row-off td { color: var(--text-tertiary); }
.path { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); }
.method { font-size: 9px; font-weight: 700; padding: 1px 4px; border-radius: 3px; }
.method.get { background: var(--success-bg); color: var(--success); }
.method.post { background: var(--warning-bg); color: var(--warning); }
.method.put { background: var(--info-bg); color: var(--info); }
.method.del { background: var(--danger-bg); color: var(--danger); }

/* 数据范围控制 */
.scope-card { border: 1.5px solid var(--brand); background: var(--brand-softer); }
.scope-desc { font-size: 11px; color: var(--text-secondary); margin-bottom: 10px; }
.scope-grid { display: flex; gap: 8px; margin-bottom: 10px; }
.scope-dim { flex: 1; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; }
.dim-header { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.dim-icon { font-size: 13px; }
.dim-name { font-size: 11px; font-weight: 600; color: var(--text); }
.dim-badge { font-size: 9px; padding: 1px 5px; border-radius: 6px; background: var(--bg-tertiary); color: var(--text-tertiary); }
.dim-options { display: flex; gap: 4px; flex-wrap: wrap; }
.dim-opt { font-size: 10px; padding: 2px 8px; border: 1px solid var(--border); border-radius: 10px; color: var(--text-secondary); }
.dim-opt.active { border-color: var(--brand); background: var(--brand-soft); color: var(--brand); font-weight: 600; }
.dim-opt.dim-disabled { opacity: 0.4; text-decoration: line-through; }
.scope-expr { background: #1e293b; border-radius: 6px; padding: 8px 12px; }
.expr-label { font-size: 10px; color: #94a3b8; margin-bottom: 3px; font-weight: 500; }
.expr-code { font-family: var(--font-mono); font-size: 11px; color: #38bdf8; }

/* 预设预览 */
.preset-list { display: flex; flex-direction: column; gap: 6px; }
.preset-item { border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; }
.preset-item.active { border-color: var(--brand); background: var(--brand-softer); }
.preset-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.preset-name { font-size: 12px; font-weight: 600; color: var(--text); }
.preset-apis { font-size: 10px; color: var(--text-tertiary); }
.preset-detail { display: flex; gap: 3px; flex-wrap: wrap; align-items: center; }
.api-tag { font-size: 9px; font-family: var(--font-mono); padding: 1px 6px; border-radius: 3px; background: var(--bg-tertiary); color: var(--text-secondary); }
.scope-tag { font-size: 9px; padding: 1px 6px; border-radius: 3px; background: var(--info-bg); color: var(--info); }
</style>
