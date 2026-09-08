import client from './client';

export const authApi = {
  login: (username: string) => client.post('/auth/login/', { username }),
  logout: () => client.post('/auth/logout/'),
  getMe: () => client.get('/auth/me/'),
};

export const userApi = {
  list: () => client.get('/users/'),
  detail: (id: number) => client.get(`/users/${id}/`),
  permissions: (id: number) => client.get(`/users/${id}/permissions/`),
};

export const orgApi = {
  tree: () => client.get('/org/tree/'),
  businessLines: {
    list: () => client.get('/org/business-lines/'),
    create: (data: any) => client.post('/org/business-lines/', data),
    update: (id: number, data: any) => client.put(`/org/business-lines/${id}/`, data),
  },
  groups: {
    list: () => client.get('/org/groups/'),
    create: (data: any) => client.post('/org/groups/', data),
    update: (id: number, data: any) => client.put(`/org/groups/${id}/`, data),
    addMember: (groupId: number, data: any) => client.post(`/org/groups/${groupId}/members/`, data),
    removeMember: (groupId: number, userId: number) =>
      client.delete(`/org/groups/${groupId}/members/${userId}/`),
    updateMember: (groupId: number, userId: number, data: any) =>
      client.patch(`/org/groups/${groupId}/members/${userId}/`, data),
  },
};

export const authzApi = {
  roles: {
    list: () => client.get('/authz/roles/'),
    create: (data: any) => client.post('/authz/roles/', data),
    update: (id: number, data: any) => client.put(`/authz/roles/${id}/`, data),
    delete: (id: number) => client.delete(`/authz/roles/${id}/`),
  },
  dataRules: {
    list: () => client.get('/authz/data-rules/'),
    create: (data: any) => client.post('/authz/data-rules/', data),
    update: (id: number, data: any) => client.put(`/authz/data-rules/${id}/`, data),
    delete: (id: number) => client.delete(`/authz/data-rules/${id}/`),
  },
  myPermissions: () => client.get('/authz/my-permissions/'),
  userPermissions: (userId: number) => client.get(`/authz/users/${userId}/permissions/`),
  groupPermissions: (groupId: number) => client.get(`/authz/groups/${groupId}/permissions/`),
  permissionRequests: {
    list: () => client.get('/authz/permission-requests/'),
    create: (data: any) => client.post('/authz/permission-requests/', data),
    myList: () => client.get('/authz/my-permission-requests/'),
    relatedList: () => client.get('/authz/related-permission-requests/'),
    approve: (id: number, action: string) =>
      client.post(`/authz/permission-requests/${id}/approve/`, { action }),
  },
  approvalConfigs: {
    list: () => client.get('/authz/approval-configs/'),
    create: (data: any) => client.post('/authz/approval-configs/', data),
    update: (id: number, data: any) => client.put(`/authz/approval-configs/${id}/`, data),
  },
  appChangeApprovalConfigs: {
    list: () => client.get('/authz/app-change-approval-configs/'),
    create: (data: any) => client.post('/authz/app-change-approval-configs/', data),
    update: (id: number, data: any) => client.put(`/authz/app-change-approval-configs/${id}/`, data),
    delete: (id: number) => client.delete(`/authz/app-change-approval-configs/${id}/`),
  },
  releaseApprovalConfigs: {
    list: () => client.get('/authz/release-approval-configs/'),
    create: (data: any) => client.post('/authz/release-approval-configs/', data),
    update: (id: number, data: any) => client.put(`/authz/release-approval-configs/${id}/`, data),
    delete: (id: number) => client.delete(`/authz/release-approval-configs/${id}/`),
  },
  approvalFlowTemplates: {
    list: (params?: any) => client.get('/authz/approval-flow-templates/', { params }),
    detail: (id: number) => client.get(`/authz/approval-flow-templates/${id}/`),
    create: (data: any) => client.post('/authz/approval-flow-templates/', data),
    update: (id: number, data: any) => client.put(`/authz/approval-flow-templates/${id}/`, data),
    delete: (id: number) => client.delete(`/authz/approval-flow-templates/${id}/`),
  },
  calculateApprovalFlow: (data: any) => client.post('/authz/calculate-approval-flow/', data),
  businessLineLeader: () => client.get('/authz/business-line-leader/'),
  checkPermission: (appId: number, envId: number) =>
    client.post('/authz/check-permission/', { app_id: appId, env_id: envId }),
  checkAccess: (data: { type: string; id: number; action: string }) =>
    client.post('/authz/check-access/', data),
  checkAccessBatch: (data: { checks: Array<{ type: string; id: number; action: string }> }) =>
    client.post('/authz/check-access-batch/', data),
  adjustDetail: (groupId: number, appId: number, envType: string) =>
    client.get(`/authz/groups/${groupId}/permission-adjust-detail/`, { params: { app_id: appId, env_type: envType } }),
  adjustSubmit: (groupId: number, data: any) =>
    client.post(`/authz/groups/${groupId}/permission-adjust-submit/`, data),
};

export const infraApi = {
  environments: {
    list: () => client.get('/infra/environments/'),
    create: (data: any) => client.post('/infra/environments/', data),
  },
  clusters: {
    list: () => client.get('/infra/clusters/'),
    create: (data: any) => client.post('/infra/clusters/', data),
  },
  namespaces: {
    list: () => client.get('/infra/namespaces/'),
  },
};

export const appApi = {
  list: (params?: any) => client.get('/apps/', { params }),
  detail: (id: number) => client.get(`/apps/${id}/`),
  create: (data: any) => client.post('/apps/', data),
  update: (id: number, data: any) => client.put(`/apps/${id}/`, data),
  delete: (id: number) => client.delete(`/apps/${id}/`),
  envConfigs: {
    list: (appId: number) => client.get(`/apps/${appId}/env-configs/`),
    create: (appId: number, data: any) => client.post(`/apps/${appId}/env-configs/`, data),
    update: (appId: number, configId: number, data: any) =>
      client.put(`/apps/${appId}/env-configs/${configId}/`, data),
  },
  resourceTree: () => client.get('/resource-tree/'),
  scale: (appId: number, data: { env_code: string; target_replicas: number; reason?: string }) =>
    client.post(`/apps/${appId}/scale/`, data),
  operations: (appId: number, data: {
    env_code: string;
    action: 'restart' | 'stop' | 'start' | 'scale' | 'traffic';
    target_replicas?: number;
    traffic_action?: 'take_out' | 'restore';
    reason?: string;
  }) => client.post(`/apps/${appId}/operations/`, data),
  branches: {
    list: (appId: number) => client.get(`/apps/${appId}/branches/`),
  },
  commits: {
    list: (appId: number, branch: string) =>
      client.get(`/apps/${appId}/commits/`, { params: { branch } }),
  },
};

export const releaseApi = {
  list: (params?: any) => client.get('/releases/', { params }),
  detail: (id: number) => client.get(`/releases/${id}/`),
  create: (data: any) => client.post('/releases/', data),
  update: (id: number, data: any) => client.put(`/releases/${id}/`, data),
  delete: (id: number) => client.delete(`/releases/${id}/`),
  submitApproval: (id: number) => client.post(`/releases/${id}/submit-approval/`),
  approveAction: (id: number, action: string, comment?: string) =>
    client.post(`/releases/${id}/approve/`, { action, comment }),
  execute: (id: number) => client.post(`/releases/${id}/execute/`),
  cancel: (id: number) => client.post(`/releases/${id}/cancel/`),
  tasks: (id: number) => client.get(`/releases/${id}/tasks/`),
  taskLogs: (releaseId: number, taskId: number) =>
    client.get(`/releases/${releaseId}/tasks/${taskId}/logs/`),
  ciLogs: (id: number) => client.get(`/releases/${id}/ci-logs/`),
  cdLogs: (id: number) => client.get(`/releases/${id}/cd-logs/`),
  executeTask: (releaseId: number, taskId: number) =>
    client.post(`/releases/${releaseId}/tasks/${taskId}/execute/`),
  retryTask: (releaseId: number, taskId: number) =>
    client.post(`/releases/${releaseId}/tasks/${taskId}/retry/`),
  rollback: (id: number) => client.post(`/releases/${id}/rollback/`),
  pipeline: (id: number) => client.get(`/releases/${id}/pipeline/`),
  verifications: (id: number) => client.get(`/releases/${id}/verifications/`),
  verify: (id: number) => client.post(`/releases/${id}/verify/`),
};

export const approvalApi = {
  list: (params?: any) => client.get('/approvals/', { params }),
  pending: (params?: any) => client.get('/approvals/pending/', { params }),
  approve: (id: number, comment?: string) =>
    client.post(`/approvals/${id}/approve/`, { comment }),
  reject: (id: number, comment?: string) =>
    client.post(`/approvals/${id}/reject/`, { comment }),
  approveStep: (id: number, comment?: string) =>
    client.post(`/approvals/${id}/approve-step/`, { comment }),
  rejectStep: (id: number, comment?: string) =>
    client.post(`/approvals/${id}/reject-step/`, { comment }),
  // 便捷方法：按权限申请子类型查询
  permissionPending: (params?: any) =>
    client.get('/approvals/pending/', { params: { ...params, type: 'permission', request_type: 'apply' } }),
  permissionList: (params?: any) =>
    client.get('/approvals/', { params: { ...params, type: 'permission', request_type: 'apply' } }),
  changePending: (params?: any) =>
    client.get('/approvals/pending/', { params: { ...params, type: 'permission', request_type: 'share,revoke,release' } }),
  changeList: (params?: any) =>
    client.get('/approvals/', { params: { ...params, type: 'permission', request_type: 'share,revoke,release' } }),
};

export const deployApi = {
  list: () => client.get('/deploy-history/'),
  detail: (id: number) => client.get(`/deploy-history/${id}/`),
  pods: (id: number) => client.get(`/deploy-history/${id}/pods/`),
  rollback: (id: number) => client.post(`/deploy-history/${id}/rollback/`),
};

export const artifactApi = {
  list: (params?: any) => client.get('/artifacts/', { params }),
  create: (data: any) => client.post('/artifacts/', data),
  detail: (id: number) => client.get(`/artifacts/${id}/`).then((res: any) => res.data || res),
  byApp: (appId: number) => client.get(`/artifacts/by-app/${appId}/`),
  promotions: (id: number) => client.get(`/artifacts/${id}/promotions/`),
  promote: (id: number) => client.post(`/artifacts/${id}/promote/`),
  repositories: {
    list: () => client.get('/artifact-repositories/'),
    create: (data: any) => client.post('/artifact-repositories/', data),
  },
};

export const configApi = {
  templates: {
    list: (params?: any) => client.get('/config-templates/', { params }),
    create: (data: any) => client.post('/config-templates/', data),
    detail: (id: number) => client.get(`/config-templates/${id}/`),
    update: (id: number, data: any) => client.put(`/config-templates/${id}/`, data),
    render: (id: number, data: any) => client.post(`/config-templates/${id}/render/`, data),
  },
  variables: {
    list: (params?: any) => client.get('/config-variables/', { params }),
    create: (data: any) => client.post('/config-variables/', data),
    update: (id: number, data: any) => client.put(`/config-variables/${id}/`, data),
  },
  variableValues: {
    list: (params?: any) => client.get('/config-variable-values/', { params }),
    update: (id: number, data: any) => client.put(`/config-variable-values/${id}/`, data),
    batchUpdate: (data: any) => client.post('/config-variable-values/batch/', data),
  },
  releases: {
    list: () => client.get('/config-releases/'),
    create: (data: any) => client.post('/config-releases/', data),
    diff: (id: number) => client.get(`/config-releases/${id}/diff/`),
    byRelease: (releaseId: number) => client.get(`/config-releases/by-release/${releaseId}/`),
  },
};

export const auditApi = {
  list: () => client.get('/audit-logs/'),
  detail: (id: number) => client.get(`/audit-logs/${id}/`),
};

export const imageApi = {
  list: () => client.get('/images/'),
  create: (data: any) => client.post('/images/', data),
  update: (id: number, data: any) => client.put(`/images/${id}/`, data),
  delete: (id: number) => client.delete(`/images/${id}/`),
};

export const knowledgeApi = {
  modules: () => client.get('/knowledge/modules/'),
  moduleDetail: (id: string) => client.get(`/knowledge/modules/${id}/`),
  article: (moduleId: string, articleId: string) => client.get(`/knowledge/articles/${moduleId}/${articleId}/`),
  interview: (moduleId: string) => client.get(`/knowledge/interviews/${moduleId}/`),
  saveInterview: (moduleId: string, data: any) => client.put(`/knowledge/interviews/${moduleId}/`, data),
  yuqueConfig: () => client.get('/knowledge/yuque-config/'),
};

export const dashboardApi = {
  stats: () => client.get('/dashboard/stats/'),
  recentReleases: () => client.get('/dashboard/recent-releases/'),
  myPendingApprovals: () => client.get('/dashboard/my-pending-approvals/'),
};