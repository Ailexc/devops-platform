import { create } from 'zustand';
import { authApi } from '../api';

interface User {
  id: number;
  username: string;
  display_name: string;
  avatar_url: string;
  is_group_leader?: boolean;
  is_audit_admin?: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  loading: false,

  login: async (username: string) => {
    const res: any = await authApi.login(username);
    localStorage.setItem('access_token', res.data.token);
    set({
      token: res.data.token,
      user: res.data.user,
    });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ user: null, token: null });
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      set({ loading: true });
      const res: any = await authApi.getMe();
      set({
        user: res.data.user,
        loading: false,
      });
    } catch {
      localStorage.removeItem('access_token');
      set({ user: null, token: null, loading: false });
    }
  },
}));