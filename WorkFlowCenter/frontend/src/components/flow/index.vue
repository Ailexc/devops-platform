<template>
  <div>
    <div class="flow-desgin">
      <section class="flow-desgin-main">
        <!-- 流程节点界面 -->
        <div class="box-scale" :style="`transform: scale(${flowStore.zoomScale / 100});`">
          <!-- 绘制节点 -->
          <NodeWrap v-model:nodeConfig="nodeConfig" v-model:flowPermission="flowPermission" />
          <div class="node-wrap">
            <div class="node-wrap-box end-node">
              <div class="title">结束</div>
              <div class="content">流程结束</div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <ApproverDrawer></ApproverDrawer>
    <CopyerDrawer></CopyerDrawer>
    <ConditionDrawer></ConditionDrawer>
    <TransactDrawer></TransactDrawer>
  </div>
</template>

<script setup>
import NodeWrap from "@/components/flow/NodeWrap.vue";
import ApproverDrawer from "@/components/flow/drawer/ApproverDrawer.vue";
import ConditionDrawer from "@/components/flow/drawer/ConditionDrawer.vue";
import CopyerDrawer from "@/components/flow/drawer/CopyerDrawer.vue";
import TransactDrawer from "@/components/flow/drawer/TransactDrawer.vue";
import { useFlowStore } from "@/stores/index";
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

const flowStore = useFlowStore();
const router = useRouter();

let nodeConfig = ref({});
let workFlowDef = ref({});
let flowPermission = ref({});
let flowWidgets = ref([]); // 作为分支条件的组件

const loadFlowData = (def) => {
  const { nodeConfig: nodeConfig0, flowPermission: flowPermission0, workFlowDef: workFlowDef0, flowWidgets: flowWidgets0 } = def;
  nodeConfig.value = nodeConfig0;
  flowPermission.value = flowPermission0;
  workFlowDef.value = workFlowDef0;
  flowWidgets.value = flowWidgets0;
  flowStore.setFlowDefId(workFlowDef0.id);
};

watch(flowPermission, () => {
  flowStore.flowDefinition.flowPermission = flowPermission.value;
});

watch(nodeConfig, () => {
  flowStore.flowDefinition.nodeConfig = nodeConfig.value;
}, { deep: true });

onMounted(async () => {
  if (flowStore.flowDefinition == undefined) {
    router.push("/flowmanindex");
  } else {
    loadFlowData(flowStore.flowDefinition);
  }
});
</script>

<style lang="less">
// @canvas-bg: #f5f5f7;
@canvas-bg: #f2f3f5;

.flow-desgin {
  height: 100%;
  z-index: 1;
  cursor: grab;
}

.flow-desgin-main {
  width: 100%;
  background-color: @canvas-bg;
  user-select: none;

  .box-scale {
    transform: scale(1);
    display: inline-block;
    position: relative;
    width: 100%;
    padding: 54.5px 0;
    -webkit-box-align: start;
    -ms-flex-align: start;
    align-items: flex-start;
    -webkit-box-pack: center;
    -ms-flex-pack: center;
    justify-content: center;
    -ms-flex-wrap: wrap;
    flex-wrap: wrap;
    min-width: -webkit-min-content;
    min-width: -moz-min-content;
    min-width: min-content;
    transform-origin: 50% 0px 0px;
  }

  .end-node {
    border-radius: 8px;
    display: flex;
    flex-direction: column;

    &::before {
      content: "";
      position: absolute;
      top: -8px;
      left: 50%;
      transform: translateX(-50%);
      width: 0;
      height: 4px;
      border-style: solid;
      border-width: 8px 6px 4px;
      border-color: #cacaca transparent transparent;
    }

    .title {
      height: 28px;
      border-radius: 8px 8px 0 0;
      background: #a9b4cd;
      padding: 0 12px;
    }

    .content {
      color: #646a73;
    }
  }
}
</style>
