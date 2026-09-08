import { ref, computed } from 'vue'
import type { TopoEdge } from '@/components/topo/types'

export interface DraftItem {
  action: 'add' | 'remove' | 'update'
  source: string
  target: string
  sourceName: string
  targetName: string
  relation_type: string
  strength: string
}

export function useRelationEditor() {
  const editMode = ref(false)
  const draft = ref<DraftItem[]>([])
  const draftVisible = ref(false)

  function toggleEdit() {
    editMode.value = !editMode.value
  }

  function addDraft(item: Omit<DraftItem, 'sourceName' | 'targetName'> & { sourceName?: string; targetName?: string }) {
    draft.value.push({
      sourceName: item.source,
      targetName: item.target,
      ...item,
    } as DraftItem)
  }

  function removeDraft(index: number) {
    draft.value.splice(index, 1)
  }

  function clearDraft() {
    draft.value = []
  }

  /** 草稿覆盖到图上的待生效边（add=待接入边；remove/update=标记原边） */
  const pendingOverlay = computed(() => {
    const edges: TopoEdge[] = []
    const removedKeys = new Set<string>()
    for (const d of draft.value) {
      const key = `${d.source}->${d.target}`
      if (d.action === 'add') {
        edges.push({
          source: d.source,
          target: d.target,
          label: '',
          strength: d.strength,
          relation_type: d.relation_type,
          pending: true,
        })
      } else {
        removedKeys.add(key)
      }
    }
    return { edges, removedKeys }
  })

  function keyOf(source: string, target: string, relation_type: string) {
    return `${source}->${target}:${relation_type}`
  }

  return {
    editMode,
    draft,
    draftVisible,
    pendingOverlay,
    toggleEdit,
    addDraft,
    removeDraft,
    clearDraft,
    keyOf,
  }
}
