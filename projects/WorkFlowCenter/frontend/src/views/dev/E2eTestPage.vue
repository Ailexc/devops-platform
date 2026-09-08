<template>
  <div class="e2e-page">
    <div class="page-header">
      <div>
        <h1>流程测试模块</h1>
        <p class="page-desc">
          每个测试工单（流程）下包含多个<b>测试场景</b>：正常完成 / 流程进行中 / 流程异常等。
          点击进入工单，选择场景即可一键跑通，并查看完整流程与测试记录。
        </p>
      </div>
    </div>

    <div v-loading="metaLoading" class="flow-grid">
      <div v-for="def in flows" :key="def.id" class="flow-card" @click="openDetail(def)">
        <div class="flow-card__head">
          <span class="flow-card__icon"><el-icon><SetUp /></el-icon></span>
          <div class="flow-card__title">
            <span class="flow-card__name">{{ def.name }}</span>
            <span class="flow-card__key">{{ def.key }}</span>
          </div>
          <el-tag size="small" effect="plain">{{ def.rules_count }} 条业务规则</el-tag>
        </div>
        <div class="flow-card__body">
          <div class="flow-card__label">测试场景（{{ def.scenarios.length }} 个）</div>
          <div v-if="def.scenarios.length" class="scenario-tags">
            <span
              v-for="s in def.scenarios"
              :key="s.key"
              class="scenario-tag"
              :class="'scenario-tag--' + s.mode"
            >
              <span class="scenario-tag__dot"></span>{{ s.name }}
            </span>
          </div>
          <div v-else class="scenario-empty">暂未配置测试场景</div>
        </div>
        <div class="flow-card__foot">
          <el-button size="small" type="primary" @click.stop="openDetail(def)">
            <el-icon><View /></el-icon>
            进入测试
          </el-button>
        </div>
      </div>
      <el-empty v-if="!metaLoading && !flows.length" description="暂无已发布流程" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SetUp, View } from '@element-plus/icons-vue'
import { getE2eMeta } from '@/api/modules/process'

const router = useRouter()
const flows = ref([])
const metaLoading = ref(false)

const openDetail = (def) => {
  router.push(`/dev/e2e-test/${def.key}`)
}

const loadMeta = async () => {
  metaLoading.value = true
  try {
    const response = await getE2eMeta()
    flows.value = response?.data ?? response ?? []
  } catch (error) {
    console.error('获取测试流程失败:', error)
    ElMessage.error('获取测试流程失败')
  } finally {
    metaLoading.value = false
  }
}

onMounted(() => {
  loadMeta()
})
</script>

<style scoped>
.e2e-page { padding: 24px; background: #f7f8fa; min-height: 100%; max-width: 1280px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-header h1 { margin: 0 0 6px; font-size: 22px; color: #1d2129; }
.page-desc { margin: 0; font-size: 13px; color: #86909c; line-height: 1.7; max-width: 760px; }

.flow-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.flow-card { background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; padding: 16px; transition: all .2s; cursor: pointer; }
.flow-card:hover { border-color: #409eff; box-shadow: 0 4px 14px rgba(64,158,255,.12); transform: translateY(-2px); }
.flow-card__head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.flow-card__icon { width: 38px; height: 38px; border-radius: 8px; background: #ecf5ff; color: #409eff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.flow-card__title { flex: 1; min-width: 0; }
.flow-card__name { font-size: 15px; font-weight: 600; color: #1d2129; display: block; }
.flow-card__key { font-size: 12px; color: #86909c; font-family: ui-monospace, monospace; }
.flow-card__body { margin-bottom: 14px; }
.flow-card__label { font-size: 12px; color: #86909c; margin-bottom: 8px; }

.scenario-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.scenario-tag { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; padding: 3px 10px; border-radius: 6px; border: 1px solid #e5e6eb; background: #f7f8fa; color: #4e5969; }
.scenario-tag__dot { width: 6px; height: 6px; border-radius: 50%; background: #c9cdd4; }
.scenario-tag--completed { color: #00b42a; border-color: #b7eb8f; background: #f2fdf5; }
.scenario-tag--completed .scenario-tag__dot { background: #00b42a; }
.scenario-tag--running { color: #165dff; border-color: #a0cfff; background: #f0f7ff; }
.scenario-tag--running .scenario-tag__dot { background: #165dff; }
.scenario-tag--abnormal { color: #f53f3f; border-color: #f3c1c1; background: #fff4f4; }
.scenario-tag--abnormal .scenario-tag__dot { background: #f53f3f; }
.scenario-tag--rejected { color: #ff7d00; border-color: #ffd091; background: #fff9ef; }
.scenario-tag--rejected .scenario-tag__dot { background: #ff7d00; }
.scenario-empty { font-size: 12px; color: #c9cdd4; }
.flow-card__foot { text-align: right; }
</style>
