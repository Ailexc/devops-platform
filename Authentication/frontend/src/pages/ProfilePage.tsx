import { App as AntApp, Button, Card, Descriptions, Form, Input, Tag } from 'antd'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'

const SOURCE_LABEL: Record<string, string> = {
  local: '本地用户库',
  ldap: 'LDAP',
  okta: 'Okta',
}

export default function ProfilePage() {
  const { message } = AntApp.useApp()
  const nav = useNavigate()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const [form] = Form.useForm()

  const onChangePassword = async (values: { old_password: string; new_password: string }) => {
    try {
      await authApi.changePassword(values.old_password, values.new_password)
      message.success('密码修改成功')
      form.resetFields()
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      message.error(detail || '密码修改失败')
    }
  }

  const refreshMe = async () => {
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      /* 忽略 */
    }
  }

  void refreshMe()

  return (
    <div className="profile-container">
      <Card title="个人信息" style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="middle">
          <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
          <Descriptions.Item label="姓名">{user?.display_name}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user?.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="部门">{user?.department || '-'}</Descriptions.Item>
          <Descriptions.Item label="手机号">{user?.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="认证来源">
            <Tag color={user?.source === 'local' ? 'blue' : user?.source === 'ldap' ? 'green' : 'purple'}>
              {SOURCE_LABEL[user?.source ?? 'local'] ?? user?.source}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="修改密码" style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          style={{ maxWidth: 420 }}
          onFinish={onChangePassword}
        >
          <Form.Item
            name="old_password"
            label="原密码"
            rules={[{ required: true, message: '请输入原密码' }]}
          >
            <Input.Password placeholder="原密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少 6 位' },
            ]}
          >
            <Input.Password placeholder="新密码（至少 6 位）" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请再次输入新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="再次输入新密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="回到门户">
        <Button type="link" onClick={() => nav('/')}>
          返回应用广场
        </Button>
      </Card>
    </div>
  )
}
