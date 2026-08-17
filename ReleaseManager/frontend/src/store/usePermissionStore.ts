import { create } from 'zustand';

interface PermissionState {
  hasDataScope: (type: string, id: number) => boolean;
}

export const usePermissionStore = create<PermissionState>(() => ({
  hasDataScope: (type: string, id: number) => {
    const perms = JSON.parse(localStorage.getItem('permissions') || '{}');
    const scope = perms.data_scope || {};
    if (type === 'business_line') return scope.business_line_ids?.includes(id) ?? true;
    if (type === 'app') return scope.app_ids?.includes(id) ?? true;
    if (type === 'env') return scope.env_ids?.includes(id) ?? true;
    return true;
  },
}));