import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Select, Button, Card, Typography, Space, Divider } from 'antd';
import { SafetyOutlined, UserOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/useAuthStore';
import { userApi } from '../../api';
import { useState } from 'react';

const { Title } = Typography;

interface UserOption {
  id: number;
  username: string;
  display_name: string;
}

export default function LoginPage() {
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(false);
  const { login, loadUser } = useAuthStore();
  const navigate = useNavigate();

  // SSO(OIDC) 回调：认证中心授权后后端 302 回 /login?token=<本地JWT> → 存 localStorage 并清理 URL
  useEffect(() => {
    const tok = new URLSearchParams(window.location.search).get('token');
    if (!tok) return;
    localStorage.setItem('access_token', tok);
    window.history.replaceState({}, '', window.location.pathname);
    useAuthStore.setState({ token: tok, user: null });
    loadUser().finally(() => navigate('/dashboard', { replace: true }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    userApi.list().then((res: any) => {
      setUsers(res.data || []);
    });
  }, []);

  const handleLogin = async (values: { username: string }) => {
    setLoading(true);
    try {
      await login(values.username);
      navigate('/dashboard');
    } catch (err) {
      console.error('Login failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: '#f0f2f5',
    }}>
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Space orientation="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={3}>发布系统 Demo</Title>
            <p style={{ color: '#999' }}>选择用户登录</p>
          </div>
          <Form onFinish={handleLogin} layout="vertical">
            <Form.Item
              name="username"
              label="选择用户"
              rules={[{ required: true, message: '请选择一个用户' }]}
            >
              <Select
                placeholder="请选择登录用户"
                size="large"
                showSearch
                optionFilterProp="label"
                options={users.map((u) => ({
                  value: u.username,
                  label: `${u.display_name} (${u.username})`,
                }))}
              />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                icon={<UserOutlined />}
              >
                登录
              </Button>
            </Form.Item>
          </Form>
          <Divider>或</Divider>
          <Button
            type="primary"
            block
            size="large"
            ghost
            icon={<SafetyOutlined />}
            href="/oauth/login"
          >
            统一认证登录（SSO · OIDC）
          </Button>
        </Space>
      </Card>
    </div>
  );
}