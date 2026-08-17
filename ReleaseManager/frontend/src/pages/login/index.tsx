import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Select, Button, Card, Typography, Space } from 'antd';
import { UserOutlined } from '@ant-design/icons';
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
  const { login } = useAuthStore();
  const navigate = useNavigate();

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
        </Space>
      </Card>
    </div>
  );
}