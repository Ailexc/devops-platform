<template>
  <div class="task-mgmt">
    <div class="b-tabs">
      <button v-for="tab in subTabs" :key="tab.id" class="b-tab" :class="{ act: activeTab === tab.id }" @click="activeTab = tab.id">
        <span class="b-ic">{{ tab.icon }}</span>{{ tab.label }}
      </button>
    </div>

    <!-- ==================== AWS 资源管理 ==================== -->
    <div v-show="activeTab === 'aws'" class="tab-content">
      <div class="mod-desc">
        <strong>☁️ AWS 资源管理</strong> — 任务配置与同步下发。区域级为主入口（两波次：先资源后关系），资源/关系级可针对性修复。🟡 = 执行中（并发锁占用）。
        <button class="btn-t btn-3" style="margin-left:8px" @click="loadTree()">🔄 刷新</button>
      </div>

      <div v-if="awsLoading" style="text-align:center;padding:40px;color:var(--t2)">
        <div class="spin"></div><div style="margin-top:10px;font-size:12px">正在加载...</div>
      </div>
      <div v-else-if="awsError" style="text-align:center;padding:12px;font-size:11px;color:var(--coral);border:1px solid rgba(239,68,68,.2);border-radius:8px;background:rgba(239,68,68,.05)">⚠️ {{ awsError }}</div>
      <template v-else>
        <!-- 账号列表 -->
        <div v-for="acct in awsAccounts" :key="acct.account_id" class="acct">
          <!-- 账号头部：整行可点击展开 -->
          <div class="acct-hd" @click="expandedAcct = expandedAcct === acct.account_id ? null : acct.account_id">
            <span class="a-icon">☁️</span>
            <span class="a-name">{{ acct.name }}</span>
            <span class="a-id">{{ acct.account_id }}</span>
            <span class="a-coverage">{{ acct.regions.length }} 区域</span>
            <span class="a-actions" @click.stop>
              <button class="btn-t btn-3" @click.stop="openConfigModal(acct)">⚙️ 配置</button>
            </span>
            <span class="a-arw" :class="{ open: expandedAcct === acct.account_id }">▼</span>
          </div>
          <!-- 区域列表 -->
          <div v-if="expandedAcct === acct.account_id" class="acct-body">
            <div v-for="reg in acct.regions" :key="reg.code" class="reg" :class="{ locked: isRegionLocked(acct.name, reg.code) }">
              <!-- 区域头部：区域 cron 统一在账号级「配置」中管理 -->
              <div class="reg-hd" @click="toggleReg(acct.account_id, reg.code)">
                <span class="r-name">{{ reg.code }}</span>
                <span v-if="isRegionLocked(acct.name, reg.code)" class="r-lock" title="该区域有任务执行中">🟡</span>
                <span class="r-actions" @click.stop>
                  <button class="btn-t btn-2" @click="runSync(acct.name, reg.code, 'region', '', 'full')">🔄 全量同步</button>
                </span>
                <span class="r-arw" :class="{ open: isRegOpen(acct.account_id, reg.code) }">▼</span>
              </div>
              <!-- 区域内容 -->
              <div v-if="isRegOpen(acct.account_id, reg.code)" class="reg-body">
                <!-- 资源分组 -->
                <div v-if="reg.resource_groups && reg.resource_groups.length > 0">
                  <div v-for="grp in reg.resource_groups" :key="grp.name" class="rg-block">
                    <div class="rg-head">
                      <span class="rg-icon">{{ groupIcon(grp.name) }}</span>
                      <span class="rg-name">{{ grp.name }}</span>
                      <span class="rg-actions">
                        <button class="btn-t btn-2" @click="runSync(acct.name, reg.code, 'group', grp.name, 'full')">🔄 组同步</button>
                      </span>
                    </div>
                    <!-- 资源卡片 -->
                    <div class="res-cards">
                      <div v-for="res in grp.resources" :key="res.name" class="res-card" :class="{ locked: isLocked(grp.name + ':' + res.name) }">
                        <div class="res-ic">{{ resourceIcon(res.name) }}</div>
                        <div class="res-info">
                          <div class="res-name">{{ res.name }}</div>
                          <div class="res-desc">{{ resourceDesc(res.name) }}</div>
                        </div>
                        <span v-if="isLocked(grp.name + ':' + res.name)" class="res-lock" title="执行中">🟡</span>
                        <div class="res-actions">
                          <button class="btn-t btn-2" @click="runSync(acct.name, reg.code, 'resource', res.name, 'full')">🔄 同步</button>
                          <button class="btn-t btn-3" @click="runSync(acct.name, reg.code, 'resource', res.name, 'incremental')">🔍 增量</button>
                        </div>
                      </div>
                    </div>
                    <!-- 关联关系卡片 -->
                    <div v-if="grp.relationships && grp.relationships.length > 0" class="rel-cards">
                      <div v-for="rel in grp.relationships" :key="rel.source + rel.target" class="rel-card-item" :class="{ locked: isLocked('rel:' + rel.source + ':' + rel.target) }">
                        <div class="rel-flow">
                          <span class="rel-entity">{{ rel.source }}</span>
                          <span class="rel-arrow">→</span>
                          <span class="rel-entity">{{ rel.target }}</span>
                          <span class="rel-num" :class="'rc-' + rel.cardinality.replace(':', '-')">{{ rel.cardinality }}</span>
                        </div>
                        <div class="rel-desc">{{ rel.desc }}</div>
                        <span v-if="isLocked('rel:' + rel.source + ':' + rel.target)" class="res-lock" title="执行中">🟡</span>
                        <div class="rel-actions">
                          <button class="btn-t btn-2 rel-sync" @click="runSync(acct.name, reg.code, 'relation', rel.source + ':' + rel.target, 'full')">🔄 同步</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="rg-empty">暂无已配置的资源类型</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ==================== 配置弹窗 ==================== -->
    <div v-if="showConfigModal" class="modal-mask" @click.self="showConfigModal=false">
      <div class="modal-box">
        <div class="modal-hd">
          <span>{{ configModalData.icon }} {{ configModalData.name }} — 区域同步配置</span>
          <span class="modal-close" @click="showConfigModal=false">✕</span>
        </div>
        <div class="modal-body">
          <table class="cfg-table">
            <thead><tr><th>区域</th><th>Cron 表达式</th><th>并发数</th></tr></thead>
            <tbody>
              <tr v-for="reg in configModalData.regions" :key="reg.code">
                <td class="cfg-region">{{ reg.code }}</td>
                <td><input class="cfg-cron" v-model="reg.cron" placeholder="0 2 * * *"></td>
                <td><input class="cfg-concur" v-model.number="reg.concurrency" type="number" min="1" max="200"></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-ft">
          <button class="btn-t btn-3" @click="showConfigModal=false">取消</button>
          <button class="btn-t btn-2" @click="saveRegionConfig">保存</button>
        </div>
      </div>
    </div>

    <!-- ==================== 增量同步弹窗 ==================== -->
    <div v-if="showDiffModal" class="modal-mask" @click.self="showDiffModal=false">
      <div class="modal-box" style="width:460px">
        <div class="modal-hd">
          <span>🔍 增量同步 — {{ diffModalData.resourceType }}</span>
          <span class="modal-close" @click="showDiffModal=false">✕</span>
        </div>
        <div class="modal-body">
          <div class="diff-info">
            <span>📦 {{ diffModalData.account }}</span>
            <span>🌐 {{ diffModalData.region }}</span>
            <span>📂 {{ diffModalData.group }}</span>
          </div>
          <div class="diff-mode-tabs">
            <button class="dm-tab" :class="{ act: diffMode === 'preview' }" @click="diffMode='preview'">🔍 预览差异并下发</button>
            <button class="dm-tab" :class="{ act: diffMode === 'ids' }" @click="diffMode='ids'">🆔 指定资源ID下发</button>
          </div>
          <div v-if="diffMode === 'preview'" class="diff-preview">
            <div class="diff-preview-desc">系统将对比 CMDB 与 AWS 实际数据，列出差异后由你确认下发。</div>
          </div>
          <div v-if="diffMode === 'ids'" class="diff-ids">
            <div class="diff-ids-desc">指定资源 ID 进行增量同步，多个 ID 用逗号分隔。</div>
            <textarea class="diff-ids-input" rows="3" placeholder="如: i-0abc1234def56789, i-0def5678abc12345"></textarea>
          </div>
        </div>
        <div class="modal-ft">
          <button class="btn-t btn-3" @click="showDiffModal=false">取消</button>
          <button v-if="diffMode==='preview'" class="btn-t btn-1" @click="showDiffModal=false">🚀 预览并下发</button>
          <button v-else class="btn-t btn-1" @click="showDiffModal=false">🚀 确认下发</button>
        </div>
      </div>
    </div>

    <!-- ==================== Lark 配置弹窗 ==================== -->
    <div v-if="showLarkModal" class="modal-mask" @click.self="showLarkModal=false">
      <div class="modal-box" style="width:460px">
        <div class="modal-hd">
          <span>📋 Lark 通讯录 — 调度配置</span>
          <span class="modal-close" @click="showLarkModal=false">✕</span>
        </div>
        <div class="modal-body">
          <div class="cfg-row">
            <label>全量同步 Cron</label>
            <input class="cfg-input" value="0 4 * * *" placeholder="0 4 * * *" />
            <div class="cfg-hint">每天凌晨 4:00 执行全量同步</div>
          </div>
          <div class="cfg-row">
            <label>增量同步间隔（分钟）</label>
            <input class="cfg-input" type="number" value="5" min="1" max="60" />
            <div class="cfg-hint">每 5 分钟检查一次增量变更</div>
          </div>
        </div>
        <div class="modal-ft">
          <button class="btn-t btn-3" @click="showLarkModal=false">取消</button>
          <button class="btn-t btn-2" @click="showLarkModal=false">保存</button>
        </div>
      </div>
    </div>

    <!-- ==================== 内部系统资源管理 ==================== -->
    <div v-show="activeTab === 'internal'" class="tab-content">
      <div class="mod-desc">
        <strong>🔌 内部系统资源管理</strong> — 将公司内部各系统的数据同步到 CMDB。系统预定义 <strong>10 个连接器</strong>。
      </div>
      <div class="fl">
        <select class="fl-s"><option>全部状态</option><option>已连接</option><option>异常</option></select>
        <input class="fl-inp" placeholder="搜索连接器...">
        <button class="btn-t btn-4" style="padding:4px 12px;font-size:10px;margin-left:auto">➕ 新增连接器</button>
      </div>
      <div class="conn-list">
        <div v-for="c in connectors" :key="c.name" class="conn-card">
          <div class="cc-ic" :style="{background: c.bg}">{{ c.icon }}</div>
          <div class="cc-body">
            <div class="cc-nm">{{ c.name }} <span class="sb" :class="c.stCls" style="font-size:8px;margin-left:6px">{{ c.stLbl }}</span></div>
            <div class="cc-desc">{{ c.desc }}</div>
            <div v-if="c.err" style="font-size:10px;color:#c0392b;margin-top:3px">⚠️ {{ c.err }}</div>
            <div class="cc-meta">
              <span>🔗 {{ c.ep }}</span>
              <span>🔐 {{ c.auth }}</span>
              <span>🔄 {{ c.freq }}</span>
            </div>
          </div>
          <div class="cc-status">
            <button class="btn-t btn-2">🔄 同步</button>
            <button class="btn-t btn-3" @click="openLarkConfig">✏️ 配置</button>
          </div>
          <span class="cc-arrow">›</span>
        </div>
      </div>
    </div>

    <!-- ==================== 巡检任务管理 ==================== -->
    <div v-show="activeTab === 'inspection'" class="tab-content">
      <div class="mod-desc">
        <strong>🔍 巡检任务管理</strong> — 定时对 CMDB 数据质量、资源合规性、配置一致性进行自动检查。系统预定义 <strong>6 个巡检项</strong>。
      </div>
      <div class="fl">
        <select class="fl-s"><option>全部类别</option><option>数据质量</option><option>安全合规</option><option>成本分析</option></select>
        <button class="btn-t btn-2" style="padding:4px 12px;font-size:10px;margin-left:auto">▶️ 执行全部巡检</button>
      </div>
      <div class="insp-grid">
        <div v-for="i in inspections" :key="i.name" class="insp-card">
          <div class="ic-h">
            <span class="ic-ic" :style="{background: i.bg}">{{ i.icon }}</span>
            <span class="ic-nm">{{ i.name }}</span>
            <span class="sb" :class="i.stCls">{{ i.stLbl }}</span>
          </div>
          <div class="ic-desc">{{ i.desc }}</div>
          <div class="ic-meta">
            <span class="ic-m-item">📂 {{ i.cat }}</span>
            <span class="ic-m-item">⏰ {{ i.sched }}</span>
            <span class="ic-m-item">🎯 {{ i.scope }}</span>
          </div>
          <div class="ic-result" :class="i.st">{{ i.result }}</div>
          <div class="ic-actions">
            <button v-if="i.st==='failed'" class="btn-t btn-6" @click.stop="confirmExecute(i.name, '重试')">🔄 重试</button>
            <button v-else class="btn-t btn-2" @click.stop="confirmExecute(i.name, '立即执行')">▶️ 立即执行</button>
            <button class="btn-t btn-3" @click="goToHistory(i.name)">📋 历史</button>
            <button class="btn-t btn-3" @click.stop="openInspConfig(i)">⚙️ 配置</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 测试任务 ==================== -->
    <div v-show="activeTab === 'testing'" class="tab-content">
      <div class="mod-desc">
        <strong>🧪 测试任务</strong> — 真实 Celery 任务端到端验证。点击执行将触发后端真实 IO 操作（网络请求/文件写入）。
      </div>

      <!-- 网络采集模拟 -->
      <div class="test-card">
        <div class="tc-head">
          <div class="tc-info">
            <div class="tc-name">🌐 网络采集模拟</div>
            <div class="tc-desc">从 jsonplaceholder 公共 API 采集用户数据，写入本地 JSON 文件</div>
          </div>
          <button class="btn-t btn-2" :disabled="testResults.network_collect?.loading" @click="runTestTask('network_collect')">
            {{ testResults.network_collect?.loading ? '⏳ 执行中...' : '🚀 执行' }}
          </button>
        </div>
        <div class="tc-params">
          <span class="tc-param">📡 请求: GET https://jsonplaceholder.typicode.com/users</span>
          <span class="tc-param">📁 输出: /tmp/cmdb_test/sync_{task_id}.json</span>
        </div>
        <!-- 结果区域 -->
        <div v-if="testResults.network_collect" class="tc-result" :class="'tc-' + testResults.network_collect.status">
          <div v-if="testResults.network_collect.status === 'completed'" class="tc-success">
            <div class="tc-row"><span class="tc-label">状态</span><span class="tc-val tc-ok">✅ 成功</span></div>
            <div class="tc-row"><span class="tc-label">Task ID</span><span class="tc-val tc-mono">{{ testResults.network_collect.task_id }}</span></div>
            <div v-if="summaryOf(testResults.network_collect.result)" class="tc-row"><span class="tc-label">结果</span><span class="tc-val">{{ summaryOf(testResults.network_collect.result) }}</span></div>
            <div v-if="statsOf(testResults.network_collect.result).length" class="tc-row">
              <span class="tc-label">指标</span><span class="tc-val">
                <template v-for="s in statsOf(testResults.network_collect.result)" :key="s.key">
                  <span class="tc-stat">{{ s.label }}: <b>{{ s.value }}{{ s.unit }}</b></span>
                </template>
              </span>
            </div>
            <div v-if="artifactsOf(testResults.network_collect.result).length" class="tc-row">
              <span class="tc-label">产物</span><span class="tc-val">
                <template v-for="a in artifactsOf(testResults.network_collect.result)" :key="a.path">
                  <a class="file-link" href="#" @click.prevent="openFilePreview(a.path)">{{ a.name }} 👁️</a>
                </template>
              </span>
            </div>
            <div class="tc-row"><span class="tc-label">耗时</span><span class="tc-val">{{ testResults.network_collect.result?.duration }}</span></div>
          </div>
          <div v-else-if="testResults.network_collect.status === 'failed'" class="tc-fail">
            <span>❌ {{ testResults.network_collect.error || '执行失败' }}</span>
          </div>
          <div v-else class="tc-pending">
            <div class="tc-spinner"></div>
            <span>任务运行中，请稍候...</span>
          </div>
        </div>
      </div>

      <!-- 本地数据质检 -->
      <div class="test-card">
        <div class="tc-head">
          <div class="tc-info">
            <div class="tc-name">📊 本地数据质检</div>
            <div class="tc-desc">读取 CMDB 演示数据，校验完整性并生成 Markdown 质检报告</div>
          </div>
          <button class="btn-t btn-2" :disabled="testResults.data_quality_check?.loading" @click="runTestTask('data_quality_check')">
            {{ testResults.data_quality_check?.loading ? '⏳ 执行中...' : '🚀 执行' }}
          </button>
        </div>
        <div class="tc-params">
          <span class="tc-param">📖 数据源: demo_store (内存)</span>
          <span class="tc-param">📁 输出: /tmp/cmdb_test/check_{task_id}.md</span>
        </div>
        <!-- 结果区域 -->
        <div v-if="testResults.data_quality_check" class="tc-result" :class="'tc-' + testResults.data_quality_check.status">
          <div v-if="testResults.data_quality_check.status === 'completed'" class="tc-success">
            <div class="tc-row"><span class="tc-label">状态</span><span class="tc-val tc-ok">✅ 成功</span></div>
            <div class="tc-row"><span class="tc-label">Task ID</span><span class="tc-val tc-mono">{{ testResults.data_quality_check.task_id }}</span></div>
            <div v-if="summaryOf(testResults.data_quality_check.result)" class="tc-row"><span class="tc-label">结果</span><span class="tc-val">{{ summaryOf(testResults.data_quality_check.result) }}</span></div>
            <div v-if="statsOf(testResults.data_quality_check.result).length" class="tc-row">
              <span class="tc-label">指标</span><span class="tc-val">
                <template v-for="s in statsOf(testResults.data_quality_check.result)" :key="s.key">
                  <span class="tc-stat">{{ s.label }}: <b>{{ s.value }}{{ s.unit }}</b></span>
                </template>
              </span>
            </div>
            <div v-if="artifactsOf(testResults.data_quality_check.result).length" class="tc-row">
              <span class="tc-label">产物</span><span class="tc-val">
                <template v-for="a in artifactsOf(testResults.data_quality_check.result)" :key="a.path">
                  <a class="file-link" href="#" @click.prevent="openFilePreview(a.path)">{{ a.name }} 👁️</a>
                </template>
              </span>
            </div>
            <div class="tc-row"><span class="tc-label">耗时</span><span class="tc-val">{{ testResults.data_quality_check.result?.duration }}</span></div>
          </div>
          <div v-else-if="testResults.data_quality_check.status === 'failed'" class="tc-fail">
            <span>❌ {{ testResults.data_quality_check.error || '执行失败' }}</span>
          </div>
          <div v-else class="tc-pending">
            <div class="tc-spinner"></div>
            <span>任务运行中，请稍候...</span>
          </div>
        </div>
      </div>

      <!-- Open Library 图书采集分析 -->
      <div class="test-card">
        <div class="tc-head">
          <div class="tc-info">
            <div class="tc-name">📚 Open Library 图书采集分析</div>
            <div class="tc-desc">从 Open Library Search API 采集 5 个主题共 ~1500 本图书数据，经过清洗去重后进行多维分析（主题分布、年代趋势、作者排行等），生成 Markdown 分析报告</div>
          </div>
          <button class="btn-t btn-2" :disabled="testResults.openlibrary_collect?.loading" @click="runTestTask('openlibrary_collect')">
            {{ testResults.openlibrary_collect?.loading ? '⏳ 执行中...' : '🚀 执行' }}
          </button>
        </div>
        <div class="tc-params">
          <span class="tc-param">📡 数据源: Open Library Search API (5 主题 × 3 页)</span>
          <span class="tc-param">⏱️ 预计耗时: 20-40s</span>
          <span class="tc-param">📁 产出: 分析报告 + 清洗后数据集</span>
        </div>
        <!-- 结果区域 -->
        <div v-if="testResults.openlibrary_collect" class="tc-result" :class="'tc-' + testResults.openlibrary_collect.status">
          <div v-if="testResults.openlibrary_collect.status === 'completed'" class="tc-success">
            <div class="tc-row"><span class="tc-label">状态</span><span class="tc-val tc-ok">✅ 成功</span></div>
            <div class="tc-row"><span class="tc-label">Task ID</span><span class="tc-val tc-mono">{{ testResults.openlibrary_collect.task_id }}</span></div>
            <div v-if="summaryOf(testResults.openlibrary_collect.result)" class="tc-row"><span class="tc-label">结果</span><span class="tc-val">{{ summaryOf(testResults.openlibrary_collect.result) }}</span></div>
            <div v-if="statsOf(testResults.openlibrary_collect.result).length" class="tc-row">
              <span class="tc-label">指标</span><span class="tc-val">
                <template v-for="s in statsOf(testResults.openlibrary_collect.result)" :key="s.key">
                  <span class="tc-stat">{{ s.label }}: <b>{{ s.value }}{{ s.unit }}</b></span>
                </template>
              </span>
            </div>
            <div v-if="detailsOf(testResults.openlibrary_collect.result).length" class="tc-row">
              <span class="tc-label">主题分布</span><span class="tc-val">
                <template v-for="t in detailsOf(testResults.openlibrary_collect.result)" :key="t.name">
                  <span class="tc-stat">{{ t.name }}: <b>{{ t.count }}</b></span>
                </template>
              </span>
            </div>
            <div v-if="artifactsOf(testResults.openlibrary_collect.result).length" class="tc-row">
              <span class="tc-label">产物</span><span class="tc-val">
                <template v-for="a in artifactsOf(testResults.openlibrary_collect.result)" :key="a.path">
                  <a class="file-link" href="#" @click.prevent="openFilePreview(a.path)">{{ a.name }} 👁️</a>
                </template>
              </span>
            </div>
            <div class="tc-row"><span class="tc-label">耗时</span><span class="tc-val">{{ testResults.openlibrary_collect.result?.duration }}</span></div>
          </div>
          <div v-else-if="testResults.openlibrary_collect.status === 'failed'" class="tc-fail">
            <span>❌ {{ testResults.openlibrary_collect.error || '执行失败' }}</span>
          </div>
          <div v-else class="tc-pending">
            <div class="tc-spinner"></div>
            <span>任务运行中，请稍候（预计 20-40 秒）...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 文件预览弹窗 ==================== -->
    <div v-if="showFilePreviewModal" class="modal-mask" @click.self="showFilePreviewModal=false">
      <div class="modal-box" style="width:640px;max-height:80vh;display:flex;flex-direction:column">
        <div class="modal-hd">
          <span>📄 {{ filePreviewData.name }}</span>
          <span class="modal-close" @click="showFilePreviewModal=false">✕</span>
        </div>
        <div class="modal-body" style="flex:1;overflow:auto;max-height:60vh">
          <div v-if="filePreviewData.loading" style="text-align:center;padding:20px;color:var(--t2)">
            <div class="spin"></div><div style="margin-top:8px;font-size:11px">加载中...</div>
          </div>
          <div v-else-if="filePreviewData.error" style="color:var(--coral);font-size:11px">❌ {{ filePreviewData.error }}</div>
          <pre v-else class="file-preview-content">{{ filePreviewData.content }}</pre>
        </div>
      </div>
    </div>

    <!-- ==================== 确认执行弹窗 ==================== -->
    <div v-if="showConfirmModal" class="modal-mask" @click.self="showConfirmModal=false">
      <div class="modal-box" style="width:400px">
        <div class="modal-hd">
          <span>{{ confirmModalData.action }} — {{ confirmModalData.name }}</span>
          <span class="modal-close" @click="showConfirmModal=false">✕</span>
        </div>
        <div class="modal-body">
          <div class="confirm-msg">确认要{{ confirmModalData.action }}「{{ confirmModalData.name }}」吗？</div>
          <div class="confirm-desc">任务执行后将立即开始巡检，请在执行历史中查看结果。</div>
        </div>
        <div class="modal-ft">
          <button class="btn-t btn-3" @click="showConfirmModal=false">取消</button>
          <button class="btn-t btn-2" @click="showConfirmModal=false">确认</button>
        </div>
      </div>
    </div>

    <!-- ==================== 巡检配置弹窗 ==================== -->
    <div v-if="showInspConfigModal" class="modal-mask" @click.self="showInspConfigModal=false">
      <div class="modal-box" style="width:460px">
        <div class="modal-hd">
          <span>⚙️ {{ inspConfigData.name }} — 调度配置</span>
          <span class="modal-close" @click="showInspConfigModal=false">✕</span>
        </div>
        <div class="modal-body">
          <div class="cfg-row">
            <label>Cron 表达式</label>
            <input class="cfg-input" :value="inspConfigData.sched" placeholder="0 6 * * *" />
            <div class="cfg-hint">当前调度：{{ inspConfigData.sched }}</div>
          </div>
          <div class="cfg-row">
            <label>超时时间（秒）</label>
            <input class="cfg-input" type="number" value="1800" min="60" max="7200" />
            <div class="cfg-hint">任务执行超时后自动终止</div>
          </div>
          <div class="cfg-row">
            <label>告警通知</label>
            <select class="cfg-input">
              <option>失败时通知</option>
              <option>始终通知</option>
              <option>关闭</option>
            </select>
          </div>
        </div>
        <div class="modal-ft">
          <button class="btn-t btn-3" @click="showInspConfigModal=false">取消</button>
          <button class="btn-t btn-2" @click="showInspConfigModal=false">保存</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toastMsg" class="toast" :class="toastType">{{ toastMsg }}</div>
    </transition>
  </div>
</template>

<script>
import { fetchTaskTree, executeTask, updateRegionConfig } from '../api/index.js'

const GROUP_ICONS = { '计算': '🖥️', '网络': '🌐', '存储': '🗄️', '安全': '🛡️', '数据库': '🗄️' }
const RESOURCE_META = {
  EC2: { icon: '🖥️', desc: '弹性计算实例' },
  SecurityGroup: { icon: '🛡️', desc: '安全组' },
  NetworkInterface: { icon: '🔗', desc: '弹性网卡' },
  VPC: { icon: '🌐', desc: '虚拟私有网络' },
  Subnet: { icon: '📡', desc: '子网' },
  RDS: { icon: '🗄️', desc: '关系型数据库' },
}

export default {
  name: 'TaskManagement',
  data() {
    return {
      activeTab: 'aws',
      subTabs: [
        { id: 'aws', icon: '☁️', label: 'AWS 资源管理' },
        { id: 'internal', icon: '🔌', label: '内部系统资源管理' },
        { id: 'inspection', icon: '🔍', label: '巡检任务管理' },
        { id: 'testing', icon: '🧪', label: '测试任务' },
      ],
      awsLoading: true,
      awsError: '',
      awsAccounts: [],
      lockedKeys: new Set(),
      expandedAcct: null,
      openRegs: {},
      // Config modal（账号级：区域 cron/并发统一在这里配置）
      showConfigModal: false,
      configModalData: { name: '', icon: '', regions: [] },
      // Toast
      toastMsg: '',
      toastType: 'ok',
      toastTimer: null,
      // Diff modal
      showDiffModal: false,
      diffMode: 'preview',
      diffModalData: { account: '', region: '', group: '', resourceType: '' },
      // Lark modal
      showLarkModal: false,
      // Confirm modal
      showConfirmModal: false,
      confirmModalData: { name: '', action: '' },
      // Inspection config modal
      showInspConfigModal: false,
      inspConfigData: { name: '', sched: '' },
      // Test tasks
      testResults: {},
      // File preview modal
      showFilePreviewModal: false,
      filePreviewData: { name: '', content: '', loading: false, error: '' },

      connectors: [
        { icon:'📋', bg:'var(--bl)', name:'Lark 通讯录', desc:'同步用户/部门/群组到CMDB', stCls:'sb-o', stLbl:'已连接', ep:'open.feishu.cn', auth:'App ID + Secret', freq:'每日04:00+增量5min', cnt:'1,247用户·38部门', last:'04:12·2m18s'},
      ],
      inspections: [
        { icon:'📋', bg:'var(--bl)', name:'CMDB 数据完整性检查', cat:'数据质量', desc:'遍历全量资源，检查必填字段缺失/关联断裂/孤儿记录', sched:'每天 06:00', scope:'CMDB 全域 2.4M 资源', stCls:'sb-o', stLbl:'✅ 正常', result:'✅ 完成·23条缺失关联·12条孤儿记录', st:'success'},
        { icon:'🔒', bg:'var(--cl)', name:'安全组开放端口审计', cat:'安全合规', desc:'检查所有安全组入站规则的高危端口暴露', sched:'每天 07:00', scope:'1,250 安全组', stCls:'sb-w', stLbl:'⚠️ 需关注', result:'⚠️ 5个安全组存在 0.0.0.0/0 入口·涉及22-3389', st:'warning'},
        { icon:'💸', bg:'var(--ol)', name:'闲置资源检测', cat:'成本分析', desc:'检测30天以上低利用率EC2/未挂载EBS/未绑定ELB', sched:'每周一 06:00', scope:'EC2/EBS/ELB', stCls:'sb-f', stLbl:'❌ 失败', result:'❌ 执行超时(30m+)·AssumeRole轮换中', st:'failed'},
        { icon:'📜', bg:'var(--al)', name:'ACM 证书到期检查', cat:'安全合规', desc:'检查ACM证书剩余有效期，提前30天告警', sched:'每天 09:00', scope:'12 张证书', stCls:'sb-w', stLbl:'⚠️ 需关注', result:'⚠️ 2张证书30天内到期·建议续期', st:'warning'},
        { icon:'🏷️', bg:'var(--pl)', name:'云资源标签合规检查', cat:'数据质量', desc:'检查EC2/RDS/ELB是否按规范打标', sched:'每天 10:00', scope:'EC2/RDS/ELB', stCls:'sb-o', stLbl:'✅ 正常', result:'✅ 156缺owner·23缺env·已通知负责人', st:'success'},
        { icon:'📈', bg:'var(--tl)', name:'成本异常分析', cat:'成本分析', desc:'基于Cost Explorer分析各账号费用趋势', sched:'每天 08:00', scope:'全账号 12 个', stCls:'sb-o', stLbl:'✅ 正常', result:'✅ 生产周环比+12%·建议审查apse1实例', st:'success'},
      ],
    }
  },
  async mounted() { await this.loadTree() },
  methods: {
    // ── 任务树（三源合并） ──
    async loadTree() {
      this.awsLoading = true
      this.awsError = ''
      try {
        const res = await fetchTaskTree()
        this.awsAccounts = (res.data && res.data.accounts) || []
        // 从 active_locks 构建锁定资源 key 集合
        const keys = new Set()
        ;(res.data?.active_locks || []).forEach(l => {
          ;(l.resource_keys || []).forEach(k => keys.add(k))
        })
        this.lockedKeys = keys
      } catch (e) {
        console.error('加载任务树失败:', e)
        this.awsError = '加载失败，请检查后端服务'
      } finally { this.awsLoading = false }
    },
    rk(a, r) { return a + ':' + r },
    isRegOpen(a, r) { return !!this.openRegs[this.rk(a, r)] },
    toggleReg(a, r) { const k = this.rk(a, r); this.openRegs = { ...this.openRegs, [k]: !this.openRegs[k] } },
    groupIcon(name) { return GROUP_ICONS[name] || '📦' },
    resourceIcon(name) { return (RESOURCE_META[name] || {}).icon || '📦' },
    resourceDesc(name) { return (RESOURCE_META[name] || {}).desc || '' },
    // 锁定状态：资源 key = `组:资源`；关系 key = `组:rel:源:目标`
    isLocked(key) { return this.lockedKeys.has(key) },
    isRegionLocked(account, region) {
      for (const acct of this.awsAccounts) {
        if (acct.name !== account) continue
        for (const reg of acct.regions) {
          if (reg.code !== region) continue
          for (const g of reg.resource_groups || []) {
            if (g.resources.some(r => this.isLocked(g.name + ':' + r.name))) return true
            if ((g.relationships || []).some(r => this.isLocked('rel:' + r.source + ':' + r.target))) return true
          }
        }
      }
      return false
    },
    // ── 同步下发（区域/资源组/资源/关系） ──
    async runSync(account, region, scope, target, mode) {
      const label = scope === 'region' ? '区域级' : scope === 'group' ? `组「${target}」` : target
      try {
        await executeTask({ account, region, scope, target, mode })
        this.toast(`✅ 已下发 ${account}/${region} ${label}${mode === 'incremental' ? '（增量）' : ''}`)
        setTimeout(() => this.loadTree(), 2500)
        return true
      } catch (e) {
        const msg = e.response?.data?.error || e.message
        this.toast(`❌ ${msg}`, 'err')
        if (e.response?.status === 409) setTimeout(() => this.loadTree(), 1000)
        return false
      }
    },
    // ── 区域配置（账号级：区域 cron/并发统一管理） ──
    openConfigModal(acct) {
      this.configModalData = { name: acct.name, icon: '☁️', regions: acct.regions || [] }
      this.showConfigModal = true
    },
    async saveRegionConfig() {
      try {
        // 逐区域保存 cron / 并发数
        for (const reg of this.configModalData.regions) {
          await updateRegionConfig({
            account: this.configModalData.name,
            region: reg.code,
            cron: reg.cron || '0 2 * * *',
            concurrency: reg.concurrency || 50,
          })
        }
        this.toast('✅ 区域配置已保存')
        this.showConfigModal = false
        this.loadTree()
      } catch (e) {
        this.toast(`❌ ${e.response?.data?.error || e.message}`, 'err')
      }
    },
    // ── 统一结果结构解析（summary/stats/artifacts/details） ──
    summaryOf(r) {
      return (r && r.summary) || ''
    },
    statsOf(r) {
      if (!r) return []
      if (Array.isArray(r.stats) && r.stats.length) return r.stats
      const skip = new Set(['children', 'params', 'logs', 'artifacts', 'details', 'summary', 'status', 'duration', 'topics', 'top_authors', 'edition_stats', 'bindings', 'results'])
      return Object.entries(r)
        .filter(([k, v]) => !skip.has(k) && ['number', 'string', 'boolean'].includes(typeof v))
        .map(([k, v]) => ({ key: k, label: k, value: String(v), unit: '' }))
    },
    artifactsOf(r) {
      if (!r) return []
      if (Array.isArray(r.artifacts) && r.artifacts.length) return r.artifacts
      const list = []
      for (const p of [r.file, r.report_file, r.data_file]) {
        if (p) list.push({ name: String(p).split('/').pop(), path: p })
      }
      return list
    },
    // openlibrary 特有：从 details.topics 提取主题分布
    detailsOf(r) {
      if (!r || !r.details || !r.details.topics) return []
      return Object.entries(r.details.topics).map(([name, count]) => ({ name, count }))
    },
    // ── Toast ──
    toast(msg, type = 'ok') {
      this.toastMsg = msg
      this.toastType = type
      clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => { this.toastMsg = '' }, 3200)
    },
    openDiffModal(account, region, group, resourceType) {
      this.diffModalData = { account, region, group, resourceType }
      this.diffMode = 'preview'
      this.showDiffModal = true
    },
    openLarkConfig() {
      this.showLarkModal = true
    },
    goToHistory(taskName) {
      this.$router.push({ path: '/history', query: { task: taskName } })
    },
    confirmExecute(name, action) {
      this.confirmModalData = { name, action }
      this.showConfirmModal = true
    },
    openInspConfig(insp) {
      this.inspConfigData = { name: insp.name, sched: insp.sched }
      this.showInspConfigModal = true
    },
    openFilePreview(filePath) {
      if (!filePath) return
      const name = filePath.split('/').pop()
      this.showFilePreviewModal = true
      this.filePreviewData = { name, content: '', loading: true, error: '' }
      import('../api/index.js').then(({ previewTestFile }) => {
        previewTestFile(filePath).then(res => {
          this.filePreviewData = { name, content: res.data.content, loading: false, error: '' }
        }).catch(e => {
          this.filePreviewData = { name, content: '', loading: false, error: e.response?.data?.error || e.message }
        })
      })
    },
    async runTestTask(taskKey) {
      import('../api/index.js').then(({ runTestTask, getTestTaskStatus }) => {
        this.testResults = { ...this.testResults, [taskKey]: { status: 'dispatching', loading: true } }
        runTestTask(taskKey).then(res => {
          const taskId = res.data.task_id
          this.testResults[taskKey] = { ...this.testResults[taskKey], status: 'running', task_id: taskId, loading: true }
          // Poll for result
          const poll = () => {
            getTestTaskStatus(taskId).then(r => {
              if (r.data.status === 'completed') {
                this.testResults[taskKey] = {
                  ...this.testResults[taskKey],
                  status: 'completed',
                  loading: false,
                  result: r.data.result,
                  task_id: taskId,
                }
              } else if (r.data.status === 'failed') {
                this.testResults[taskKey] = {
                  ...this.testResults[taskKey],
                  status: 'failed',
                  loading: false,
                  error: r.data.error,
                  task_id: taskId,
                }
              } else {
                setTimeout(poll, 800)
              }
            }).catch(e => {
              this.testResults[taskKey] = {
                ...this.testResults[taskKey],
                status: 'failed',
                loading: false,
                error: e.message,
              }
            })
          }
          setTimeout(poll, 500)
        }).catch(e => {
          this.testResults[taskKey] = { status: 'failed', loading: false, error: e.message }
        })
      })
    },
  },
}
</script>

<style scoped>
.b-tabs{display:flex;gap:4px;margin-bottom:12px;background:var(--card);border-radius:var(--rs);border:1px solid var(--border);padding:4px;overflow-x:auto}
.b-tab{padding:9px 20px;font-size:12px;font-weight:500;border:none;background:none;cursor:pointer;color:var(--t2);border-radius:6px;display:flex;align-items:center;gap:6px;white-space:nowrap}
.b-tab:hover{color:var(--text);background:var(--bg)}
.b-tab.act{background:var(--bl);color:var(--blue);font-weight:600}
.tab-content{display:block}
.mod-desc{font-size:11px;color:var(--t2);margin-bottom:10px;line-height:1.6;padding:8px 12px;background:var(--card);border-radius:var(--rs);border:1px solid var(--border)}
.mod-desc strong{color:var(--text)}
.fl{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;align-items:center}
.fl-s{padding:4px 10px;border:1px solid var(--border);border-radius:5px;font-size:11px;background:var(--card)}
.fl-inp{padding:4px 10px;border:1px solid var(--border);border-radius:5px;font-size:11px;background:var(--card);min-width:140px}
.spin{width:24px;height:24px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:sp .8s linear infinite;margin:0 auto}
@keyframes sp{to{transform:rotate(360deg)}}
.btn-t{font-size:9px;padding:3px 10px;border-radius:4px;font-weight:600;border:none;cursor:pointer;white-space:nowrap}
.btn-1{background:var(--blue);color:#fff}
.btn-2{background:var(--teal);color:#fff}
.btn-3{background:var(--border);color:var(--text)}
.btn-4{background:var(--pl);color:var(--purple)}
.btn-6{background:var(--cl);color:#c0392b}
.btn-t:hover{opacity:.85}
.sb{font-size:9px;padding:1px 7px;border-radius:5px;font-weight:600;display:inline-block}
.sb-o{background:var(--tl);color:#1a7a6e}
.sb-f{background:var(--cl);color:#c0392b}
.sb-w{background:var(--al);color:#a67c00}

/* Account */
.acct{background:var(--card);border-radius:var(--radius);border:1px solid var(--border);margin-bottom:8px;overflow:hidden}
.acct-hd{display:flex;align-items:center;gap:10px;padding:11px 16px;cursor:pointer;user-select:none}
.acct-hd:hover{background:var(--bg)}
.a-icon{font-size:15px}
.a-name{font-size:13px;font-weight:600;flex:1}
.a-id{font-size:9px;color:var(--t2);font-family:'SF Mono',monospace}
.a-coverage{font-size:10px;font-weight:600}
.a-actions{display:flex;gap:4px;align-items:center}
.a-arw{font-size:9px;color:var(--t2);transition:transform .2s}
.a-arw.open{transform:rotate(180deg)}
.acct-body{border-top:1px solid var(--border);padding:6px 12px 10px}

/* Region */
.reg{border:1px solid var(--border);border-radius:var(--rs);margin-bottom:5px;overflow:hidden;background:var(--bg)}
.reg-hd{display:flex;align-items:center;gap:8px;padding:7px 10px;cursor:pointer;user-select:none}
.reg-hd:hover{background:rgba(0,0,0,.03)}
.r-name{font-size:11px;font-weight:600;min-width:100px;font-family:'SF Mono',monospace}
.r-actions{margin-left:auto}
.r-arw{font-size:8px;color:var(--t2);transition:transform .2s;margin-left:4px}
.r-arw.open{transform:rotate(180deg)}
.reg-body{border-top:1px solid var(--border);padding:6px 10px 8px}

/* Resource Group Block */
.rg-block{margin-bottom:10px}
.rg-block:last-child{margin-bottom:0}
.rg-head{display:flex;align-items:center;gap:6px;margin-bottom:8px}
.rg-icon{font-size:12px}
.rg-name{font-size:11px;font-weight:600;color:var(--t2)}
.rg-actions{margin-left:auto;display:flex;gap:3px;flex-shrink:0}
.rg-empty{padding:10px;text-align:center;font-size:11px;color:var(--t2);font-style:italic}
@keyframes blink{50%{opacity:.3}}
.reg.locked{border-color:var(--orange)}
.r-cron{font-size:9px;color:var(--orange);background:rgba(245,158,11,.08);padding:1px 6px;border-radius:4px;font-family:'SF Mono',monospace;white-space:nowrap}
.r-lock{font-size:10px;animation:blink 1.2s infinite}

/* Resource Cards */
.res-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.res-card{display:flex;align-items:center;gap:12px;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:10px;transition:border-color .15s,box-shadow .15s}
.res-card:hover{border-color:var(--blue);box-shadow:0 3px 12px rgba(67,97,238,.1)}
.res-card.locked{border-color:var(--orange);background:rgba(245,158,11,.04)}
.res-ic{font-size:20px;width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:var(--bg);border-radius:10px;flex-shrink:0}
.res-info{flex:1;min-width:0}
.res-name{font-size:13px;font-weight:700;color:var(--text)}
.res-desc{font-size:10px;color:var(--t2);margin-top:1px}
.res-lock{font-size:11px;flex-shrink:0;animation:blink 1.2s infinite}
.res-actions{display:flex;gap:6px;flex-shrink:0}

/* Relationship Cards */
.rel-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px;margin-top:10px}
.rel-card-item{display:flex;align-items:center;gap:10px;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:10px;transition:border-color .15s,box-shadow .15s}
.rel-card-item:hover{border-color:var(--blue);box-shadow:0 3px 12px rgba(67,97,238,.1)}
.rel-card-item.locked{border-color:var(--orange);background:rgba(245,158,11,.04)}
.rel-flow{display:flex;align-items:center;gap:6px;flex-shrink:0}
.rel-entity{font-weight:700;white-space:nowrap;font-size:11px}
.rel-arrow{color:var(--t2);flex-shrink:0}
.rel-num{font-size:8px;padding:1px 6px;border-radius:3px;font-weight:700;font-family:'SF Mono',monospace;flex-shrink:0}
.rc-n-1{background:var(--tl);color:#1a7a6e}
.rc-1-n{background:var(--bl);color:var(--blue)}
.rc-n-n{background:var(--pl);color:var(--purple)}
.rel-desc{color:var(--t2);font-size:10px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rel-actions{display:flex;gap:6px;flex-shrink:0}

/* Modal */
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;z-index:100}
.modal-box{background:var(--card);border-radius:var(--radius);width:520px;max-width:90vw;box-shadow:0 8px 40px rgba(0,0,0,.18)}
.modal-hd{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--border);font-size:13px;font-weight:700}
.modal-close{cursor:pointer;color:var(--t2);font-size:14px;padding:2px 6px;border-radius:4px}
.modal-close:hover{background:var(--bg)}
.modal-body{padding:14px 18px}
.modal-ft{display:flex;justify-content:flex-end;gap:6px;padding:10px 18px;border-top:1px solid var(--border)}

/* Config Table */
.cfg-table{width:100%;border-collapse:collapse;font-size:11px}
.cfg-table th,.cfg-table td{padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)}
.cfg-table th{font-size:9px;font-weight:600;color:var(--t2);text-transform:uppercase;letter-spacing:.3px}
.cfg-region{font-family:'SF Mono',monospace;font-weight:500}
.cfg-cron{padding:3px 8px;border:1px solid var(--border);border-radius:4px;font-size:10px;font-family:'SF Mono',monospace;width:140px;background:var(--card)}
.cfg-concur{padding:3px 8px;border:1px solid var(--border);border-radius:4px;font-size:10px;width:60px;background:var(--card)}

/* Diff Modal */
.diff-info{display:flex;gap:10px;font-size:11px;color:var(--t2);margin-bottom:12px;padding:6px 10px;background:var(--bg);border-radius:6px}
.diff-mode-tabs{display:flex;gap:4px;margin-bottom:12px}
.dm-tab{flex:1;padding:8px 12px;font-size:11px;font-weight:500;border:1px solid var(--border);border-radius:6px;cursor:pointer;background:var(--card);color:var(--t2);text-align:center}
.dm-tab:hover{border-color:var(--blue);color:var(--text)}
.dm-tab.act{background:var(--bl);border-color:var(--blue);color:var(--blue);font-weight:600}
.diff-preview-desc{font-size:11px;color:var(--t2);line-height:1.6;padding:10px;background:var(--bg);border-radius:6px}
.diff-ids-desc{font-size:11px;color:var(--t2);margin-bottom:8px}
.diff-ids-input{width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:11px;font-family:'SF Mono',monospace;resize:vertical;background:var(--card);box-sizing:border-box}
.diff-ids-input:focus{outline:none;border-color:var(--blue)}

/* Lark Config */
.cfg-row{margin-bottom:10px}
.cfg-row label{display:block;font-size:10px;font-weight:600;color:var(--t2);margin-bottom:3px;text-transform:uppercase;letter-spacing:.3px}
.cfg-input{width:100%;padding:6px 10px;border:1px solid var(--border);border-radius:5px;font-size:11px;background:var(--card);box-sizing:border-box}
.cfg-input:focus{outline:none;border-color:var(--blue)}
.cfg-hint{font-size:9px;color:var(--t2);margin-top:3px}

/* Confirm Modal */
.confirm-msg{font-size:12px;font-weight:600;color:var(--text);margin-bottom:8px}
.confirm-desc{font-size:11px;color:var(--t2);line-height:1.6}

/* Test Tasks */
.test-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;margin-bottom:10px}
.test-card:hover{box-shadow:0 2px 12px rgba(0,0,0,.05)}
.tc-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.tc-name{font-size:13px;font-weight:700;color:var(--text);margin-bottom:2px}
.tc-desc{font-size:11px;color:var(--t2)}
.file-link{color:var(--blue);text-decoration:none;cursor:pointer;font-family:'SF Mono',monospace;font-size:10px}
.file-link:hover{text-decoration:underline;opacity:.8}
.file-preview-content{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:12px;font-size:11px;line-height:1.6;white-space:pre-wrap;word-break:break-all;margin:0;font-family:'SF Mono',monospace;max-height:55vh;overflow:auto}
.tc-params{display:flex;gap:14px;font-size:10px;color:var(--t2);margin-bottom:10px;padding:8px 10px;background:var(--bg);border-radius:6px;flex-wrap:wrap}
.tc-param{white-space:nowrap}
.tc-result{border-radius:var(--rs);padding:12px 14px;border:1px solid var(--border);margin-top:8px}
.tc-success{border-color:rgba(46,196,182,.3);background:rgba(46,196,182,.03)}
.tc-fail{border-color:rgba(239,68,68,.3);background:rgba(239,68,68,.03);color:var(--coral);font-size:11px}
.tc-pending{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--t2)}
.tc-spinner{width:16px;height:16px;border:2px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:sp .8s linear infinite;flex-shrink:0}
.tc-row{display:flex;align-items:baseline;gap:8px;padding:3px 0;font-size:11px;border-bottom:1px solid var(--border)}
.tc-row:last-child{border-bottom:none}
.tc-label{font-weight:600;color:var(--t2);min-width:70px;flex-shrink:0}
.tc-val{color:var(--text)}
.tc-ok{color:var(--teal);font-weight:600}
.tc-err{color:var(--coral);font-weight:600}
.tc-mono{font-family:'SF Mono',monospace;font-size:10px;color:var(--blue)}
.tc-stat{display:inline-flex;align-items:baseline;gap:2px;background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:2px 8px;margin-right:6px;font-size:10px;color:var(--t2)}
.tc-stat b{color:var(--text);font-size:11px}

/* Connector Cards */
.conn-list{display:flex;flex-direction:column;gap:6px}
.conn-card{display:flex;align-items:center;gap:14px;padding:13px 18px;background:var(--card);border-radius:var(--rs);border:1px solid var(--border);transition:all .15s}
.conn-card:hover{border-color:var(--blue);box-shadow:0 2px 10px rgba(67,97,238,.08)}
.cc-ic{font-size:22px;width:42px;height:42px;display:flex;align-items:center;justify-content:center;border-radius:10px;flex-shrink:0}
.cc-body{flex:1;min-width:0}
.cc-nm{font-size:13px;font-weight:600;display:flex;align-items:center;gap:8px}
.cc-desc{font-size:11px;color:var(--t2);margin-top:2px}
.cc-meta{display:flex;gap:14px;margin-top:5px;font-size:10px;color:var(--t2);flex-wrap:wrap}
.cc-status{display:flex;gap:6px;align-items:center;flex-shrink:0}
.cc-arrow{font-size:11px;color:var(--border);margin-left:4px}

/* Inspection Cards */
.insp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:8px}
.insp-card{background:var(--card);border-radius:var(--rs);border:1px solid var(--border);padding:14px 16px}
.insp-card:hover{border-color:var(--blue);box-shadow:0 2px 10px rgba(67,97,238,.08)}
.ic-h{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.ic-ic{font-size:16px;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px}
.ic-nm{font-size:13px;font-weight:600;flex:1}
.ic-desc{font-size:11px;color:var(--t2);margin-bottom:8px;line-height:1.6}
.ic-meta{display:flex;flex-wrap:wrap;gap:8px;font-size:10px;color:var(--t2);margin-bottom:8px}
.ic-m-item{display:flex;align-items:center;gap:4px}
.ic-result{background:var(--bg);border-radius:6px;padding:8px 10px;font-size:10px;margin-bottom:8px;line-height:1.6;font-family:'SF Mono',monospace}
.ic-result.success{color:#1a7a6e}
.ic-result.warning{color:#a67c00}
.ic-result.failed{color:#c0392b}
.ic-actions{display:flex;gap:6px}

/* Toast */
.toast{position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:1000;padding:9px 18px;border-radius:8px;font-size:12px;font-weight:600;box-shadow:0 6px 24px rgba(0,0,0,.18);max-width:80vw}
.toast.ok{background:#0f766e;color:#fff}
.toast.err{background:#c0392b;color:#fff}
.toast-enter-active,.toast-leave-active{transition:all .25s}
.toast-enter-from,.toast-leave-to{opacity:0;transform:translateX(-50%) translateY(-8px)}
</style>
