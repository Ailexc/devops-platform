<template>
  <a-drawer
    v-if="visible"
    :append-to-body="true"
    :width="540"
    :visible="visible"
    :closable="false"
    @cancel="close()"
    @ok="saveTransactor()"
    ok-text="保存">
    <template #title>
      <EditableText :value="flowNodeConfig.name" @change="onNodeNameChange" />
    </template>

    <div class="transact-drawer__content">
      <!-- 办理人设置 -->
      <div class="transact-setting-tip-wrapper">
        <div class="content-wrap">
          <div class="item-content">
            <div class="item-wrap tip">
              <div class="item-key-wrapper">
                <p class="item-key">办理人设置</p>
              </div>
              <div class="more-info">
                <p>当流程中某个节点不需要审批，但需要对审批单进行业务办理时，可设置办理人节点，场景如财务打款、处理盖章等。</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 办理人选择界面 -->
      <div class="transact-editor-tab-wrapper">
        <a-radio-group type="button" v-model="viewEditorType" size="large">
          <a-radio :value="0">设置办理人</a-radio>
          <a-radio :value="1">表单权限</a-radio>
          <a-radio :value="2">操作权限</a-radio>
          <a-radio :value="3">任务配置</a-radio>
        </a-radio-group>

        <!-- 设置办理人 -->
        <div class="item-content-editor" v-if="viewEditorType == 0">
          <div class="content-wrap">
            <div class="item-content">
              <!-- 办理人列表 -->
              <div class="item-wrap approver">
                <div class="transactor-list">
                  <div class="transactor-wrapper" v-for="(item, idx) in flowNodeConfig.transactors || []">
                    <div class="header">
                      <span>办理人{{ idx + 1 }}</span>
                      <icon-delete :style="{ fontSize: '18px' }" @click="delTransactor(item)" v-if="(flowNodeConfig.transactors || []).length > 1" />
                    </div>
                    <div class="main-content">
                      <a-radio-group class="radio-group" v-model="item.transactorType" @change="onTransactorTypeChanged(item)">
                        <a-grid :cols="3" :colGap="0" :rowGap="10">
                          <a-grid-item><a-radio :value="ASSIGNEE.SELF">发起人本人</a-radio></a-grid-item>
                          <a-grid-item><a-radio :value="ASSIGNEE.SUPERIOR">上级</a-radio></a-grid-item>
                          <a-grid-item><a-radio :value="ASSIGNEE.DEPARTMENT_LEADER">部门负责人</a-radio></a-grid-item>
                          <a-grid-item><a-radio :value="ASSIGNEE.ROLE">角色</a-radio></a-grid-item>
                          <a-grid-item><a-radio :value="ASSIGNEE.ASSIGNEE">指定成员</a-radio></a-grid-item>
                          <a-grid-item><a-radio :value="ASSIGNEE.INITIATOR_CHOICE" :disabled="haveMultiNode">发起人自选</a-radio></a-grid-item>
                        </a-grid>
                      </a-radio-group>
                    </div>
                    <div class="sub-content" v-if="![ASSIGNEE.SELF, ASSIGNEE.INITIATOR_CHOICE].includes(item.transactorType)">
                      <div class="sub-content-top-line"></div>
                      <template v-if="item.transactorType == ASSIGNEE.SUPERIOR">
                        <p class="bold">请选择上级</p>
                        <a-form-item label="发起人的">
                          <a-select placeholder="请选择上级" v-model="item.layer">
                            <template #header>
                              <div class="switch-container">
                                <div class="select-tip">从直属上级向上选择</div>
                                <a-link @click="switchLayerType(item)">
                                  <template #icon><icon-swap /></template>{{ item.layerType == 0 ? "切为最高上级向下" : "切为直属上级向上" }}
                                </a-link>
                              </div>
                            </template>
                            <a-option v-for="i in 20" :value="i - 1">
                              <template v-if="item.layerType == 0">{{ i == 1 ? "直属上级" : "直属上级加 " + (i - 1) + " 级" }}</template>
                              <template v-else>{{ i == 1 ? "最高上级" : "最高上级减 " + (i - 1) + " 级" }}</template>
                            </a-option>
                          </a-select>
                        </a-form-item>
                      </template>
                      <template v-else-if="item.transactorType == ASSIGNEE.DEPARTMENT_LEADER">
                        <p class="bold">请选择部门负责人</p>
                        <a-form-item label="发起人的">
                          <a-select placeholder="请选择部门负责人" v-model="item.layer">
                            <template #header>
                              <div class="switch-container">
                                <div class="select-tip">从直属部门负责人向上选择</div>
                                <a-link @click="switchLayerType(item)">
                                  <template #icon><icon-swap /></template>{{ item.layerType == 0 ? "切为最高部门向下" : "切为直属部门向上" }}
                                </a-link>
                              </div>
                            </template>
                            <a-option v-for="i in 20" :value="i - 1">
                              <template v-if="item.layerType == 0">
                                {{ i == 1 ? "直属部门负责人" : "直属部门负责人加 " + (i - 1) + " 级" }}
                              </template>
                              <template v-else>{{ i == 1 ? "最高部门负责人" : "最高部门负责人减 " + (i - 1) + " 级" }}</template>
                            </a-option>
                          </a-select>
                        </a-form-item>
                      </template>
                      <template v-else-if="item.transactorType == ASSIGNEE.ROLE">
                        <p class="bold">选择角色</p>
                        <a-form-item tooltip="请选择角色" label="组织角色">
                          <a-select multiple placeholder="请选择角色" v-model="item.roles">
                            <a-option v-for="role in allRoles" :value="role.id" :label="role.name"></a-option>
                          </a-select>
                        </a-form-item>
                      </template>
                      <template v-else-if="item.transactorType == ASSIGNEE.ASSIGNEE">
                        <p class="bold">添加成员<span>（不能超过 25 人）</span></p>
                        <div class="assignee-box">
                          <a-button size="small" @click="onAssigneeClick(item)"><icon-plus /></a-button>
                          <span class="assignee-list">
                            <a-tag v-for="userId in item.assignees">{{ getUserById(userId).name }}</a-tag>
                          </span>
                          <OrganChooseBox
                            v-if="showChooseTransactor"
                            v-model:visible="showChooseTransactor"
                            v-model:selected="selectedAssignee.assignees"
                            :hidden-dept="true"
                            :hidden-role="true" />
                        </div>
                      </template>
                    </div>
                  </div>
                </div>

                <!-- 添加办理人按钮 -->
                <div class="add-operator">
                  <a-link @click="addTransactor()" v-if="!onlyOneNode">
                    <template #icon><icon-plus /></template>添加办理人
                  </a-link>
                </div>
              </div>

              <!-- 会签、或签、序签 -->
              <div class="item-wrap sign-type" v-if="haveMultiNode || isInitiatorChoiceOrRoleOrAssignee">
                <div class="item-key-wrapper">
                  <div class="item-key">多人办理时采用的处理方式</div>
                </div>
                <div class="item-content">
                  <a-radio-group direction="vertical" v-model="flowNodeConfig.multiInstanceApprovalType">
                    <a-radio :value="1">会签（需所有办理人同意）</a-radio>
                    <a-radio :value="2">或签（一名办理人同意即可）</a-radio>
                    <a-radio :value="3" v-if="isSameTransactorType">依次办理（按顺序依次办理）</a-radio>
                  </a-radio-group>
                </div>
              </div>

              <!-- 办理人为空时 -->
              <div class="item-wrap approver-null">
                <div class="item-key-wrapper">
                  <div class="item-key">办理人为空时</div>
                </div>
                <div class="item-content">
                  <a-radio-group v-model="flowNodeConfig.flowNodeNoAuditorType" @change="onNoTransactorTypeChanged">
                    <a-radio :value="1">指定人员办理</a-radio>
                    <a-radio :value="2">转交给审批管理员</a-radio>
                  </a-radio-group>

                  <div class="approver-null-select-box">
                    <a-form-item label="指定成员" v-if="flowNodeConfig.flowNodeNoAuditorType == 1">
                      <a-select placeholder="请选择成员" v-model="flowNodeConfig.flowNodeNoAuditorAssignee">
                        <a-option v-for="user in allUsers" :value="user.id" :label="user.name"></a-option>
                      </a-select>
                    </a-form-item>
                    <a-form-item label="审批管理员" v-else-if="flowNodeConfig.flowNodeNoAuditorType == 2">
                      <a-select placeholder="请选择管理员" v-model="flowNodeConfig.flowNodeAuditAdmin">
                        <a-option v-for="userId in workFlowDef.flowAdminIds" :value="userId" :label="getUserById(userId).name" />
                      </a-select>
                    </a-form-item>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 设置表单权限 -->
        <NodeFormAuthSetting v-model:flowNodeConfig="flowNodeConfig" v-else-if="viewEditorType == 1"></NodeFormAuthSetting>
        <!-- 设置操作权限 -->
        <div class="item-content-auth" v-else-if="viewEditorType == 2">
          <div class="content-wrap">
            <div class="item-content">
              <div class="item-wrap auth-list">
                <a-checkbox class="auth-item" v-model="flowNodeConfig.assignable" :value="1">允许转交</a-checkbox>
              </div>
            </div>
          </div>
        </div>
        <!-- 任务配置 -->
        <div class="item-content-auth" v-else-if="viewEditorType == 3">
          <div class="content-wrap">
            <div class="item-content">
              <!-- 执行方式 -->
              <div class="item-wrap task-mode">
                <div class="item-key-wrapper">
                  <p class="item-key">执行方式</p>
                </div>
                <a-radio-group type="button" v-model="flowNodeConfig.taskConfig.mode" @change="onTaskModeChange">
                  <a-radio value="manual">人工办理</a-radio>
                  <a-radio value="confirm">自动执行+人工确认</a-radio>
                  <a-radio value="auto">完全自动执行</a-radio>
                </a-radio-group>
                <div class="task-bind-desc">人工办理：人处理实际业务；自动+确认：先生成确认待办，随机办理人确认后执行动作；完全自动：系统直接执行，异常才转人工</div>
              </div>

              <template v-if="flowNodeConfig.taskConfig.mode != 'manual'">
                <!-- 执行顺序 -->
                <div class="item-wrap task-order">
                  <div class="item-key-wrapper">
                    <p class="item-key">执行顺序</p>
                  </div>
                  <a-radio-group type="button" v-model="flowNodeConfig.taskConfig.executionMode">
                    <a-radio value="sequential">串行执行</a-radio>
                    <a-radio value="parallel">并行执行</a-radio>
                  </a-radio-group>
                  <div class="task-bind-desc">串行：动作依次执行，前序动作输出可被后续动作引用；并行：全部动作同时执行，全部完成后统一判定</div>
                </div>

                <!-- 动作列表 -->
                <div class="item-wrap task-actions">
                  <div class="item-key-wrapper">
                    <p class="item-key">执行动作</p>
                    <a-link @click="addAction"><template #icon><icon-plus /></template>添加动作</a-link>
                  </div>
                  <div class="action-list">
                    <div class="action-card" v-for="(action, idx) in flowNodeConfig.taskConfig.actions" :key="action.key">
                      <div class="action-card__header">
                        <span>动作 {{ idx + 1 }}</span>
                        <div class="action-card__ops">
                          <a-link v-if="idx > 0" @click="moveAction(idx, -1)">上移</a-link>
                          <a-link v-if="idx < flowNodeConfig.taskConfig.actions.length - 1" @click="moveAction(idx, 1)">下移</a-link>
                          <icon-delete :style="{ fontSize: '16px' }" @click="removeAction(action)" />
                        </div>
                      </div>
                      <a-form-item label="能力">
                        <a-select
                          v-model="action.capabilityId"
                          placeholder="选择要自动执行的能力"
                          allow-search
                          @change="(id) => onActionCapabilityChange(action, id)"
                        >
                          <a-option v-for="cap in capabilities" :key="cap.id" :value="cap.id">
                            {{ cap.name }}（{{ cap.code }}）{{ cap.execute_mode === 'async' ? '· 异步' : '· 同步' }}
                          </a-option>
                        </a-select>
                        <div class="task-bind-desc" v-if="capabilities.length == 0">
                          暂无可用能力，请在「能力注册」中先注册能力
                        </div>
                        <div v-if="actionCapabilityMode(action)" class="task-bind-desc" :style="{ color: actionCapabilityMode(action) === 'async' ? '#eb0aa1' : '#00b42a' }">
                          {{ actionCapabilityMode(action) === 'async' ? '⚡ 异步执行：提交到任务队列即返回，执行结果经队列消息/回调回写' : '✔ 同步执行：流程阻塞等待执行完成' }}
                        </div>
                      </a-form-item>
                      <a-form-item label="动作名称">
                        <a-input v-model="action.name" placeholder="如：创建主机" />
                      </a-form-item>

                      <!-- 字段映射 -->
                      <template v-if="actionInputProps(action).length">
                        <p class="bold bind-title">字段映射</p>
                        <div class="field-bind-list">
                          <div class="field-bind-item" v-for="bind in action.fieldBindings" :key="bind.capabilityField">
                            <div class="bind-cap-field">
                              <span class="bind-field-name">{{ bind.capabilityField }}</span>
                              <span class="bind-field-type">{{ typeLabel(bind.capabilityType) }}</span>
                            </div>
                            <div class="bind-source-row">
                              <a-select v-model="bind.source" size="small" class="source-select">
                                <a-option value="form">表单字段</a-option>
                                <a-option value="upstream">上游返回</a-option>
                                <a-option value="constant">常量</a-option>
                                <a-option v-if="flowNodeConfig.taskConfig.executionMode == 'sequential'" value="previous">前序动作</a-option>
                              </a-select>
                              <a-select
                                v-if="bind.source == 'form'"
                                v-model="bind.formField"
                                placeholder="选择表单字段"
                                allow-search
                                class="bind-target"
                              >
                                <a-option v-for="w in flowWidgets" :key="w.name" :value="w.name">{{ w.label }}</a-option>
                              </a-select>
                              <div v-else-if="bind.source == 'upstream'" class="upstream-row">
                                <a-select
                                  v-model="bind.upstreamNode"
                                  placeholder="上游节点"
                                  allow-search
                                  class="bind-target"
                                >
                                  <a-option v-for="n in upstreamNodes" :key="n.key" :value="n.key">{{ n.name }}</a-option>
                                </a-select>
                                <a-input
                                  v-model="bind.upstreamField"
                                  placeholder="输出字段名，如 host_id"
                                  class="bind-target"
                                />
                              </div>
                              <a-input
                                v-else-if="bind.source == 'constant'"
                                v-model="bind.constant"
                                placeholder="常量值"
                                class="bind-target"
                              />
                              <div v-else-if="bind.source == 'previous'" class="upstream-row">
                                <a-select
                                  v-model="bind.previousActionKey"
                                  placeholder="前序动作"
                                  allow-search
                                  class="bind-target"
                                >
                                  <a-option v-for="a in priorActions(idx)" :key="a.key" :value="a.key">
                                    {{ a.name || a.capabilityName || a.key }}
                                  </a-option>
                                </a-select>
                                <a-input
                                  v-model="bind.previousField"
                                  placeholder="输出字段名"
                                  class="bind-target"
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </template>
                      <div class="task-bind-desc" v-else>该能力无输入参数</div>
                    </div>
                  </div>
                  <div class="task-bind-desc">动作执行过程会完整记录日志，可在申请详情的流程节点中查看</div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import EditableText from "@/components/common/EditableText.vue";
import { useFlowStore, useOrganStore } from "@/stores/index";
import { IconDelete, IconPlus, IconSwap } from "@arco-design/web-vue/es/icon";
import { computed, onBeforeMount, onMounted, ref, toRaw, watch } from "vue";
import { storeToRefs } from "pinia";
import ArrayUtil from "../common/ArrayUtil";
import { ASSIGNEE } from "../common/FlowConstant";
import Snowflake from "../common/Snowflake";
import OrganChooseBox from "../dialog/OrganChooseBox.vue";
import NodeFormAuthSetting from "../NodeFormAuthSetting.vue";
import { getCapabilities } from "@/api/modules/capability";

let flowStore = useFlowStore();
// 注意：Pinia 直接解构 state 得到的是非响应式的快照，必须用 storeToRefs
const organStore = useOrganStore();
const { roles: allRoles, users: allUsers } = storeToRefs(organStore);
const { getUserById } = organStore;
let { showTransactorDrawer, setTransactorConfig } = flowStore;
let isTransactorDrawerOpened = computed(() => flowStore.isTransactorDrawerOpened);
let transactorConfig0 = computed(() => flowStore.transactorConfig0);
let workFlowDef = computed(() => flowStore.flowDefinition.workFlowDef);
let visible = computed({
  get: () => isTransactorDrawerOpened.value,
  set: () => close(),
});

let viewEditorType = ref(0); // 界面编辑类型 0:办理人; 1:表单权限; 2:操作权限; 3:任务绑定
let _uid = ref(0);
let flowNodeConfig = ref({});

// 可选能力列表（用于任务绑定）
const capabilities = ref([]);
let flowWidgets = computed(() => flowStore.flowDefinition.flowWidgets || []);

async function loadCapabilities() {
  try {
    const resp = await getCapabilities({ page_size: 200 });
    const data = resp?.data ?? resp;
    const list = Array.isArray(data) ? data : data?.results || [];
    capabilities.value = list;
  } catch (error) {
    console.warn("加载能力列表失败（任务绑定将不可用）:", error);
    // Demo 兜底能力，保证后端未启动时任务绑定仍可体验
    capabilities.value = [
      { id: "demo_1", code: "notify_owner", name: "通知负责人" },
      { id: "demo_2", code: "run_shell", name: "执行脚本任务" },
      { id: "demo_3", code: "sync_ticket", name: "同步工单状态" },
    ];
  }
}

// 能力 JSON Schema 解析：返回属性列表
function schemaProperties(schema) {
  const props = schema?.properties || {};
  const required = schema?.required || [];
  return Object.entries(props).map(([name, p]) => ({
    name,
    title: p.title || name,
    type: p.type || "string",
    itemsType: p.items?.type || "",
    required: required.includes(name),
  }));
}

// 字段类型展示
function typeLabel(t) {
  const map = { string: "字符串", integer: "整数", number: "数字", boolean: "布尔", array: "数组", object: "对象" };
  return map[t] || t || "";
}

// 确保 taskConfig 结构完整
function ensureTaskConfig(node) {
  if (!node) return;
  const old = node.taskConfig || {};
  node.taskConfig = {
    mode: old.mode || "manual", // 执行方式：manual 人工办理 / auto 自动执行
    executionMode: old.executionMode || "sequential", // 串行 / 并行
    actions: Array.isArray(old.actions) ? old.actions : [], // 动作列表
  };
}

// 动作输入属性（按能力 schema）
const actionInputProps = (action) => {
  if (!action?.capabilityId) return [];
  const cap = capabilities.value.find((c) => String(c.id) === String(action.capabilityId));
  return cap ? schemaProperties(cap.input_schema) : [];
};

// 规范化名称用于智能预匹配
const normalizeName = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]/g, "");

// 智能预匹配：能力字段名与表单字段名/标签做相似匹配
const smartMatch = (capField, capType) => {
  const nf = normalizeName(capField);
  if (!nf) return "";
  for (const w of flowWidgets.value) {
    const name = normalizeName(w.name);
    const label = normalizeName(w.label);
    if (name === nf || label === nf) return w.name;
  }
  // 类型兼容兜底：数字类字段优先匹配数字/金额
  for (const w of flowWidgets.value) {
    const name = normalizeName(w.name);
    if (name && (nf.includes(name) || name.includes(nf))) return w.name;
  }
  return "";
};

// 依据能力输入属性重建动作字段绑定（保留已配置 + 智能预匹配）
function syncActionBindings(action) {
  const props = actionInputProps(action);
  const existing = {};
  (action.fieldBindings || []).forEach((b) => {
    if (b.capabilityField) existing[b.capabilityField] = b;
  });
  action.fieldBindings = props.map((p) => {
    const old = existing[p.name];
    if (old) {
      return { ...old, capabilityField: p.name, capabilityType: p.type };
    }
    return {
      capabilityField: p.name,
      capabilityType: p.type,
      source: "form",
      formField: smartMatch(p.name, p.type),
      upstreamNode: "",
      upstreamField: "",
      previousActionKey: "",
      previousField: "",
      constant: "",
    };
  });
  const cap = capabilities.value.find((c) => String(c.id) === String(action.capabilityId));
  if (cap) {
    action.capabilityCode = cap.code;
    action.capabilityName = cap.name;
  }
}

const onActionCapabilityChange = (action, id) => {
  if (!id) return;
  const cap = capabilities.value.find((c) => String(c.id) === String(id));
  if (cap) {
    action.capabilityCode = cap.code;
    action.capabilityName = cap.name;
    action.capabilityMode = cap.execute_mode || '';
  }
  syncActionBindings(action);
};

// 动作当前所选能力的执行模式（同步/异步）
const actionCapabilityMode = (action) => {
  if (!action?.capabilityId) return '';
  const cap = capabilities.value.find((c) => String(c.id) === String(action.capabilityId));
  return cap?.execute_mode || action.capabilityMode || '';
};

const addAction = () => {
  const actions = flowNodeConfig.value.taskConfig.actions;
  actions.push({
    key: "act_" + (actions.length + 1) + "_" + Date.now(),
    name: "",
    capabilityId: "",
    capabilityCode: "",
    capabilityName: "",
    fieldBindings: [],
  });
};

const removeAction = (action) => {
  const actions = flowNodeConfig.value.taskConfig.actions;
  const idx = actions.findIndex((a) => a.key === action.key);
  if (idx > -1) actions.splice(idx, 1);
};

const moveAction = (idx, dir) => {
  const actions = flowNodeConfig.value.taskConfig.actions;
  const target = idx + dir;
  if (target < 0 || target >= actions.length) return;
  const tmp = actions[idx];
  actions[idx] = actions[target];
  actions[target] = tmp;
};

const priorActions = (idx) => flowNodeConfig.value.taskConfig.actions.slice(0, idx);

const onTaskModeChange = () => {
  if (flowNodeConfig.value.taskConfig.mode === "manual") return;
  if (!flowNodeConfig.value.taskConfig.actions.length) {
    addAction();
  }
};

// 上游节点（当前办理节点之前的节点，用于「上游返回字段」绑定）
let nodeKey = null;
const upstreamNodes = computed(() => {
  const def = flowStore.flowDefinition;
  const all = [];
  function walk(node) {
    if (!node) return;
    all.push(node);
    for (const branch of node.conditionNodes || []) walk(branch);
    walk(node.childNode);
  }
  walk(def?.nodeConfig);
  if (!nodeKey) return [];
  const currentIdx = all.findIndex((n) => n.key === nodeKey);
  if (currentIdx === -1) return [];
  return all.slice(0, currentIdx);
});

// 是否为单个办理人节点
let onlyOneNode = computed(() => {
  const transactors = flowNodeConfig.value.transactors || [];
  if (!transactors.length) return false;
  let fristAssigneeType = transactors[0]?.transactorType;
  return [ASSIGNEE.INITIATOR_CHOICE].includes(fristAssigneeType);
});

// 是否含有多个办理人
let haveMultiNode = computed(() => {
  return (flowNodeConfig.value.transactors || []).length > 1;
});

// 是否设置了发起人自选，角色，指定办理人
let isInitiatorChoiceOrRoleOrAssignee = computed(() => {
  const transactors = flowNodeConfig.value.transactors || [];
  if (!transactors.length) return false;
  let fristAssigneeType = transactors[0]?.transactorType;
  return [ASSIGNEE.ROLE, ASSIGNEE.ASSIGNEE, ASSIGNEE.INITIATOR_CHOICE].includes(fristAssigneeType);
});

// 多个审批人设置的类型是否一致, 类型一致时才会有依次办理
let isSameTransactorType = computed(() => {
  if ((flowNodeConfig.value.transactors || []).length == 1) return false;
  let haveSameType = true;
  let tmpAssigneeType = flowNodeConfig.value.transactors[0].transactorType;
  for (let i = 1; i < flowNodeConfig.value.transactors.length; i++) {
    let tmpAssignee = flowNodeConfig.value.transactors[i];
    if (tmpAssigneeType != tmpAssignee.transactorType) {
      haveSameType = false;
      break;
    }
  }
  // 如果不能使用序签，则默认会签
  if (!haveSameType) {
    if (flowNodeConfig.value.multiInstanceApprovalType == 3) {
      flowNodeConfig.value.multiInstanceApprovalType = 1;
    }
  }
  return haveSameType;
});

// 办理人选择指定成员
let showChooseTransactor = ref(false); // 是否显示指定成员对话框
let selectedAssignee = ref({}); // 当前选中的单个办理人设置
const onAssigneeClick = (item) => {
  selectedAssignee.value = item;
  showChooseTransactor.value = true;
};

watch(transactorConfig0, (val) => {
  flowNodeConfig.value = val.value;
  ensureTaskConfig(flowNodeConfig.value);
  nodeKey = val.nodeKey;
  viewEditorType.value = 0;
  _uid = val.id;
});

watch(
  flowNodeConfig,
  (newVal) => {
    const transactors = newVal?.transactors || [];
    if (transactors.length == 1) {
      // 只设置了一个办理人
      let fristAssigneeType = transactors[0]?.transactorType;

      // 是否设置了发起人自选，角色，指定办理人
      if (
        [ASSIGNEE.ROLE, ASSIGNEE.ASSIGNEE, ASSIGNEE.INITIATOR_CHOICE].includes(fristAssigneeType) &&
        [0, 3].includes(flowNodeConfig.value.multiInstanceApprovalType)
      ) {
        if (flowNodeConfig.value.multiInstanceApprovalType == 0) {
          flowNodeConfig.value.multiInstanceApprovalType = 1;
        }
      }
    } else {
      // 如果设置了多个办理人，默认会签
      if (flowNodeConfig.value.multiInstanceApprovalType == 0) {
        flowNodeConfig.value.multiInstanceApprovalType = 1;
      }
    }
  },
  { deep: true }
);

// 切换上级和部门负责人的人事层级关系
const switchLayerType = (assignee) => {
  assignee.layerType = assignee.layerType == 0 ? 1 : 0;
};

// 办理人类型切换时
const onTransactorTypeChanged = (assignee) => {
  console.log("办理人类型切换时", assignee);
  let { transactorType } = assignee;
  if ([1, 2].includes(transactorType)) {
    assignee.layerType = 0;
    assignee.layer = 0;
    delete assignee.roles;
    delete assignee.transactors;
  } else if ([0, 7].includes(transactorType)) {
    delete assignee.layerType;
    delete assignee.layer;
    delete assignee.roles;
    delete assignee.transactors;
  } else if ([3].includes(transactorType)) {
    delete assignee.layerType;
    delete assignee.layer;
    delete assignee.transactors;
  } else if ([4].includes(transactorType)) {
    assignee.transactors = [];
    delete assignee.layerType;
    delete assignee.layer;
    delete assignee.roles;
  }
};

// 节点办理人为空选项改变时
const onNoTransactorTypeChanged = (type) => {
  if (type == 1) {
    delete flowNodeConfig.value.flowNodeAuditAdmin;
  } else if (type == 2) {
    delete flowNodeConfig.value.flowNodeNoAuditorAssignee;
  } else {
    delete flowNodeConfig.value.flowNodeNoAuditorAssignee;
    delete flowNodeConfig.value.flowNodeAuditAdmin;
  }
};

// 添加办理人
const addTransactor = () => {
  if (!flowNodeConfig.value.transactors) flowNodeConfig.value.transactors = [];
  flowNodeConfig.value.transactors.push({
    rid: Snowflake.generate(),
    transactorType: 0,
  });
};

// 删除办理人
const delTransactor = (approver) => {
  if (!flowNodeConfig.value.transactors) return;
  ArrayUtil.remove(flowNodeConfig.value.transactors, "rid", approver.rid);
  // 当设置的办理人删除到一个时。节点类型设置为：非多实例审批
  if (flowNodeConfig.value.transactors.length === 1) {
    flowNodeConfig.value.multiInstanceApprovalType = 0;
  }
};

// 编辑节点名称
const onNodeNameChange = (name) => {
  flowNodeConfig.value.name = name;
  saveTransactor(false);
};

const saveTransactor = (leave = true) => {
  setTransactorConfig({
    value: toRaw(flowNodeConfig.value),
    flag: true,
    id: _uid,
  });
  leave && close();
};

const close = () => {
  showTransactorDrawer(false);
};

onBeforeMount(() => {});
onMounted(() => {
  loadCapabilities();
});
</script>

<style lang="less">
.transact-drawer__content {
  user-select: none;

  .transact-editor-tab-wrapper {
    margin-top: 24px;

    .item-content-editor,
    .item-content-auth {
      margin-top: 8px;

      .transactor-list {
        .transactor-wrapper {
          border: 1px solid #e4e5e7;
          border-radius: 6px;
          overflow: hidden;

          + .transactor-wrapper {
            margin-top: 6px;
          }

          .header {
            padding: 0 16px;
            background: #f5f6f7;
            height: 36px;
            line-height: 36px;
            display: flex;
            justify-content: space-between;
            align-items: center;

            span {
              color: #1f2329;
              font-weight: 600;
            }

            .arco-icon {
              cursor: pointer;
              &:hover {
                color: #3370ff;
              }
            }
          }

          // .main-content {
          // }

          .sub-content {
            padding: 0 16px 10px;

            .sub-content-top-line {
              border-top: 1px solid #dee0e3;
            }

            p {
              padding-top: 10px;
              color: #1f2329;
              font-size: 14px;
              font-weight: 600;
              margin-bottom: 8px;

              span {
                color: #8f959e;
                font-weight: 400;
                font-size: 13px;
              }
            }

            .arco-form-item {
              margin-bottom: 0;
            }

            .assignee-box {
              display: flex;
              align-items: center;
              justify-content: space-between;

              .assignee-list {
                flex: 1;
                margin-left: 10px;
                display: flex;
                flex-wrap: wrap;
                gap: 4px;

                .arco-tag {
                  height: 28px;
                }
              }
            }
          }

          .radio-group {
            padding: 10px 16px;
            width: 100%;

            .arco-radio {
              margin-right: 2px;
            }
          }
        }
      }

      .add-operator {
        margin-top: 8px;
      }

      .approver-null-select-box {
        margin-top: 8px;
      }

      .auth-list {
        display: flex;
        flex-direction: column;

        .auth-item {
          margin-top: 10px;
        }
      }
    }
  }

  .arco-radio-group-button {
    width: 100%;

    .arco-radio-button {
      flex: 1;
      text-align: center;
    }
  }

  .item-key-wrapper {
    .item-key {
      color: #1f2329;
      font-weight: 600;
    }
  }

  .item-content {
    margin-top: 8px;

    .item-wrap {
      + .item-wrap {
        margin-top: 24px;
      }
    }

    .more-info {
      line-height: 20px;
      color: #646a73;
      font-weight: 400;

      p {
        position: relative;
        padding-left: 10px;
        margin-top: 8px;

        &::before {
          content: "";
          width: 4px;
          height: 4px;
          position: absolute;
          top: 9px;
          left: 0;
          border-radius: 2px;
          background: #3370ff;
        }
      }
    }
  }
}

.switch-container {
  user-select: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  margin: 0 12px;

  .select-tip {
    color: #646a73;
  }
}

/* 任务绑定 */
.task-bind-switch {
  .task-bind-control {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-top: 8px;
  }
}

.task-bind-desc {
  font-size: 12px;
  line-height: 18px;
  color: #86909c;
}

.task-bind-type,
.task-bind-target,
.task-bind-name {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e5e6eb;
}

/* 能力属性展示 */
.capability-schema,
.field-bindings,
.proxy-assignee {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e5e6eb;

  .item-key-wrapper {
    margin-bottom: 8px;
  }
}

.capability-schema__body {
  .schema-title {
    margin: 8px 0 4px;
    font-size: 13px;
    font-weight: 600;
    color: #1d2129;
  }

  .schema-empty {
    padding: 8px 0;
    font-size: 12px;
    color: #86909c;
  }
}

/* 能力字段绑定 */
.field-bind-list {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .field-bind-item {
    border: 1px solid #e5e6eb;
    border-radius: 6px;
    padding: 10px 12px;

    .bind-cap-field {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      .bind-field-name {
        font-weight: 600;
        color: #1d2129;
      }

      .bind-field-type {
        font-size: 12px;
        color: #86909c;
        background: #f2f3f5;
        border-radius: 4px;
        padding: 0 6px;
      }
    }

    .bind-source-row {
      display: flex;
      align-items: center;
      gap: 8px;

      .bind-target {
        flex: 1;
        min-width: 0;
      }

      .upstream-row {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
  }
}
</style>
