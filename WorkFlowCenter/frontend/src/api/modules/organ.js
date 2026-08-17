import request from '../request'
import { useOrganStore } from '@/stores'

let cache = { loaded: false }

const pageSize = 200

/**
 * 拉取分页列表（兼容 DRF PageNumberPagination 返回 { count, next, previous, results }）
 */
async function fetchAll(url, params = {}) {
  const list = []
  let page = 1
  while (true) {
    const resp = await request.get(url, { params: { ...params, page, page_size: pageSize } })
    const data = resp?.data ?? resp
    if (Array.isArray(data)) {
      list.push(...data)
      break
    }
    const results = data?.results ?? []
    list.push(...results)
    if (!data?.next) break
    page += 1
  }
  return list
}

function normalizeUser(user) {
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.username || user.name
  return { id: user.id, name: fullName, username: user.username }
}

export async function listUsers() {
  const users = await fetchAll('/users')
  return users.map(normalizeUser)
}

export async function listDepts() {
  const depts = await fetchAll('/departments')
  return depts.map((d) => ({ id: d.id, name: d.name, parent: d.parent }))
}

export async function listRoles() {
  const roles = await fetchAll('/roles')
  return roles.map((r) => ({ id: r.id, name: r.name }))
}

/**
 * 加载组织架构数据（用户 / 部门 / 角色）到 organ store
 */
export async function loadOrgan() {
  if (cache.loaded) return
  const organStore = useOrganStore()
  try {
    const [depts, roles, users] = await Promise.all([listDepts(), listRoles(), listUsers()])
    organStore.setDepts(depts)
    organStore.setRoles(roles)
    organStore.setUsers(users)
    cache.loaded = true
  } catch (error) {
    console.warn('加载组织架构失败（流程设计器将使用空数据）:', error)
    // Demo 兜底数据：后端未启动时设计器仍可操作
    organStore.setDepts([{ id: 1, name: '研发部' }, { id: 2, name: '运营部' }])
    organStore.setRoles([{ id: 1, name: '管理员' }, { id: 2, name: '部门主管' }])
    organStore.setUsers([
      { id: 1, name: '管理员', username: 'admin' },
      { id: 2, name: '张三', username: 'zhangsan' },
      { id: 3, name: '李四', username: 'lisi' },
    ])
    // 注意：失败时不设置 cache.loaded = true，下次调用重新尝试加载真实组织数据
  }
}

export default { listUsers, listDepts, listRoles, loadOrgan }
