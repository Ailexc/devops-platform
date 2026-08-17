import axios from 'axios';

// 使用相对路径，通过 nginx 反代到 backend
// 开发环境：Vite dev server 会代理 /api 到 backend
// 生产环境：Nginx 会代理 /api 到 backend
const API_BASE = '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 自动添加 JWT
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 统一处理错误
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);

export default client;