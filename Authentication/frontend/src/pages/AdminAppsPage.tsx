import {
  AlertOutlined,
  ApiOutlined,
  ApartmentOutlined,
  AppstoreAddOutlined,
  AppstoreOutlined,
  CheckSquareOutlined,
  CloudServerOutlined,
  CodeOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  ReloadOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App as AntApp,
  Button,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Steps,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { appApi } from '../api/client'
import { useAuthStore } from '../store/auth'
import type { AppCreateResult, AppInfo, AppPayload } from '../types'

// ---------- 图标选择 ----------
const ICON_OPTIONS: { value: string; label: string; icon: React.ReactNode }[] = [
  { value: 'AppstoreOutlined', label: '应用', icon: <AppstoreOutlined /> },
  { value: 'CheckSquareOutlined', label: '任务', icon: <CheckSquareOutlined /> },
  { value: 'CloudServerOutlined', label: '云', icon: <CloudServerOutlined /> },
  { value: 'ApartmentOutlined', label: '流程', icon: <ApartmentOutlined /> },
  { value: 'AlertOutlined', label: '告警', icon: <AlertOutlined /> },
  { value: 'RocketOutlined', label: '发布', icon: <RocketOutlined /> },
  { value: 'SafetyCertificateOutlined', label: '安全', icon: <SafetyCertificateOutlined /> },
  { value: 'ExperimentOutlined', label: '实验', icon: <ExperimentOutlined /> },
  { value: 'FileTextOutlined', label: '文档', icon: <FileTextOutlined /> },
  { value: 'DatabaseOutlined', label: '数据库', icon: <DatabaseOutlined /> },
  { value: 'CodeOutlined', label: '代码', icon: <CodeOutlined /> },
  { value: 'ApiOutlined', label: 'API', icon: <ApiOutlined /> },
  { value: 'ToolOutlined', label: '工具', icon: <ToolOutlined /> },
]

function renderIcon(name: string) {
  return ICON_OPTIONS.find((i) => i.value === name)?.icon ?? <AppstoreOutlined />
}

const SSO_LABEL: Record<string, string> = { token: 'token 跳转', oidc: 'OIDC（预留）' }
const MODE_LABEL: Record<string, string> = {
  gateway: '统一网关 forwardAuth',
  direct: '直连 JWKS 自验签',
}

// ---------- 接入配置说明 ----------
function ConfigNotes({ app }: { app: AppCreateResult }) {
  const jwks = `${window.location.origin}/.well-known/jwks.json`
  const items: { key: string; label: string; content: React.ReactNode }[] = []
  if (app.sso_type === 'oidc') {
    items.push({
      key: 'oidc',
      label: 'OIDC 授权码',
      content: (
        <>
          <div>前端发起授权：携带 <Typography.Text code>client_id={app.client_id}</Typography.Text> 跳转认证中心 /authorize。</div>
          <div>后端换 token：用 <Typography.Text code>client_secret</Typography.Text> + 授权码调 /token（client_secret 仅存应用后端，勿外泄）。</div>
        </>
      ),
    })
  } else if (app.access_mode === 'gateway') {
    items.push({
      key: 'gateway',
      label: '经统一网关',
      content: (
        <>
          <div>将该应用的 <Typography.Text code>/api/*</Typography.Text> 流量纳入统一网关，配置 forwardAuth。</div>
          <div>网关校验统一 JWT 后注入 <Typography.Text code>X-Auth-*</Typography.Text> 头，业务后端直接读头取身份。</div>
        </>
      ),
    })
  } else {
    items.push({
      key: 'direct',
      label: '直连自验签',
      content: (
        <>
          <div>业务后端加一个 JWT 验签中间件，用认证中心公钥本地验签。</div>
          <div>公钥地址：<Typography.Text code copyable>{jwks}</Typography.Text></div>
        </>
      ),
    })
  }
  items.push({
    key: 'sso',
    label: '统一凭证',
    content: (
      <>
        <div>统一 JWT 由认证中心签发（RS256），可在多个系统间共用。</div>
        <div>验证端点：<Typography.Text code copyable>{`${window.location.origin}/api/auth/verify`}</Typography.Text></div>
      </>
    ),
  })
  return (
    <Descriptions column={1} bordered size="small" items={items.map((i) => ({ key: i.key, label: i.label, children: i.content }))} />
  )
}

// ---------- 注册向导（新增应用） ----------
function RegisterWizard({
  open,
  onClose,
  onDone,
}: {
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const [step, setStep] = useState(0)
  const [creating, setCreating] = useState(false)
  const [result, setResult] = useState<AppCreateResult | null>(null)

  useEffect(() => {
    if (open) {
      form.resetFields()
      setStep(0)
      setResult(null)
    }
  }, [open, form])

  const submit = async () => {
    try {
      const values = await form.validateFields()
      setCreating(true)
      const payload: AppPayload = {
        app_id: values.app_id,
        name: values.name,
        description: values.description ?? '',
        icon: values.icon ?? 'AppstoreOutlined',
        home_url: values.home_url ?? '',
        sso_type: values.sso_type ?? 'token',
        access_mode: values.access_mode ?? 'gateway',
        enabled: true,
        sort_order: values.sort_order ?? 0,
      }
      const { data } = await appApi.create(payload)
      setResult(data)
      setStep(1)
      message.success('应用已注册，凭证已发放')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      message.error(detail || '注册失败')
    } finally {
      setCreating(false)
    }
  }

  const steps = [
    { title: '基本信息' },
    { title: '应用凭证' },
    { title: '接入配置' },
    { title: '完成' },
  ]

  return (
    <Modal
      open={open}
      title="接入新应用（注册向导）"
      width={680}
      onCancel={onClose}
      footer={
        step === 0 ? (
          <Space>
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" loading={creating} onClick={submit}>
              注册并发放凭证
            </Button>
          </Space>
        ) : step < 3 ? (
          <Button type="primary" onClick={() => setStep(step + 1)}>
            下一步
          </Button>
        ) : (
          <Button
            type="primary"
            onClick={() => {
              onClose()
              onDone()
            }}
          >
            完成
          </Button>
        )
      }
    >
      <Steps current={step} size="small" items={steps} style={{ marginBottom: 24 }} />

      {step === 0 && (
        <Form form={form} layout="vertical" initialValues={{ sso_type: 'token', access_mode: 'gateway', sort_order: 0 }}>
          <Form.Item name="app_id" label="应用标识（唯一，如 my-app）" rules={[{ required: true, message: '请输入应用标识' }]}>
            <Input placeholder="my-app" />
          </Form.Item>
          <Form.Item name="name" label="应用名称" rules={[{ required: true, message: '请输入应用名称' }]}>
            <Input placeholder="我的应用" />
          </Form.Item>
          <Form.Item name="description" label="应用描述">
            <Input placeholder="一句话说明用途" />
          </Form.Item>
          <Form.Item name="home_url" label="首页地址（门户跳转目标）">
            <Input placeholder="http://localhost:xxxx" />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Select
              options={ICON_OPTIONS.map((o) => ({
                value: o.value,
                label: (
                  <Space>
                    {o.icon}
                    {o.label}
                  </Space>
                ),
              }))}
            />
          </Form.Item>
          <Space size="large" style={{ width: '100%' }}>
            <Form.Item name="sso_type" label="SSO 类型">
              <Select
                style={{ width: 220 }}
                options={[
                  { value: 'token', label: 'token 跳转' },
                  { value: 'oidc', label: 'OIDC（预留）' },
                ]}
              />
            </Form.Item>
            <Form.Item name="access_mode" label="接入方式">
              <Select
                style={{ width: 220 }}
                options={[
                  { value: 'gateway', label: '经统一网关 forwardAuth' },
                  { value: 'direct', label: '直连 JWKS 自验签' },
                ]}
              />
            </Form.Item>
            <Form.Item name="sort_order" label="排序">
              <InputNumber min={0} />
            </Form.Item>
          </Space>
        </Form>
      )}

      {step === 1 && result && (
        <div>
          <Alert type="warning" showIcon style={{ marginBottom: 16 }} message="请妥善保存以下凭证" description="client_secret 仅此一次展示，之后不再可见，请复制并保存在应用后端配置中，切勿泄露。" />
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="client_id（公开标识）">
              <Typography.Text code copyable>{result.client_id}</Typography.Text>
            </Descriptions.Item>
            <Descriptions.Item label="client_secret（机密，仅应用后端保存）">
              <Typography.Text code copyable style={{ color: '#b45309' }}>
                {result.client_secret}
              </Typography.Text>
            </Descriptions.Item>
          </Descriptions>
        </div>
      )}

      {step === 2 && result && <ConfigNotes app={result} />}

      {step === 3 && result && (
        <Alert type="success" showIcon message="应用已上架" description={`「${result.name}」已出现在统一门户的应用广场。用户登录门户后点击即可进入。`} />
      )}
    </Modal>
  )
}

// ---------- 应用管理页 ----------
export default function AdminAppsPage() {
  const { message } = AntApp.useApp()
  const user = useAuthStore((s) => s.user)
  const [apps, setApps] = useState<AppInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [editing, setEditing] = useState<AppInfo | null>(null)
  const [editForm] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await appApi.manage()
      setApps(data)
    } catch {
      message.error('加载应用列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const toggle = async (app: AppInfo, enabled: boolean) => {
    try {
      await appApi.update(app.app_id, { enabled })
      message.success(enabled ? '已启用' : '已禁用')
      load()
    } catch {
      message.error('操作失败')
    }
  }

  const remove = async (app: AppInfo) => {
    try {
      await appApi.remove(app.app_id)
      message.success('已删除')
      load()
    } catch {
      message.error('删除失败')
    }
  }

  const openEdit = (app: AppInfo) => {
    setEditing(app)
    editForm.setFieldsValue(app)
  }

  const saveEdit = async () => {
    if (!editing) return
    try {
      const values = await editForm.validateFields()
      await appApi.update(editing.app_id, values as Partial<AppPayload>)
      message.success('已保存')
      setEditing(null)
      load()
    } catch {
      message.error('保存失败')
    }
  }

  const columns: ColumnsType<AppInfo> = [
    {
      title: '应用',
      key: 'app',
      render: (_, app) => (
        <Space>
          <span style={{ fontSize: 20 }}>{renderIcon(app.icon)}</span>
          <span>
            <div style={{ fontWeight: 600 }}>{app.name}</div>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {app.app_id}
            </Typography.Text>
          </span>
        </Space>
      ),
    },
    { title: 'SSO 类型', dataIndex: 'sso_type', width: 120, render: (v: string) => <Tag>{SSO_LABEL[v] ?? v}</Tag> },
    {
      title: '接入方式',
      dataIndex: 'access_mode',
      width: 170,
      render: (v: string) =>
        v === 'direct' ? <Tag color="purple">{MODE_LABEL[v]}</Tag> : <Tag color="blue">{MODE_LABEL[v]}</Tag>,
    },
    {
      title: 'client_id',
      dataIndex: 'client_id',
      ellipsis: true,
      render: (v: string) => (v ? <Typography.Text code copyable>{v}</Typography.Text> : '-'),
    },
    { title: '排序', dataIndex: 'sort_order', width: 70 },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 90,
      render: (_, app) => (
        <Switch checked={app.enabled} checkedChildren="启用" unCheckedChildren="禁用" onChange={(c) => toggle(app, c)} />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_, app) => (
        <Space>
          <Button size="small" onClick={() => openEdit(app)}>
            编辑
          </Button>
          <Popconfirm title={`删除「${app.name}」？`} onConfirm={() => remove(app)}>
            <Button size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (!user?.is_admin) {
    return <Alert type="warning" showIcon message="需要管理员权限" description="只有管理员可以管理应用接入。" style={{ maxWidth: 640, margin: 48 }} />
  }

  return (
    <main className="profile-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>应用管理（开发者控制台）</h3>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={load}>
            刷新
          </Button>
          <Button type="primary" icon={<AppstoreAddOutlined />} onClick={() => setWizardOpen(true)}>
            接入新应用
          </Button>
        </Space>
      </div>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="应用接入流程：注册应用 → 发放凭证 → 配置接入 → 上架应用广场 → 用户 SSO 进入"
      />

      <Table<AppInfo> rowKey="id" loading={loading} columns={columns} dataSource={apps} pagination={false} />

      <RegisterWizard open={wizardOpen} onClose={() => setWizardOpen(false)} onDone={load} />

      <Modal
        open={!!editing}
        title="编辑应用"
        onCancel={() => setEditing(null)}
        onOk={saveEdit}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="应用名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input />
          </Form.Item>
          <Form.Item name="home_url" label="首页地址">
            <Input />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Select
              options={ICON_OPTIONS.map((o) => ({
                value: o.value,
                label: (
                  <Space>
                    {o.icon}
                    {o.label}
                  </Space>
                ),
              }))}
            />
          </Form.Item>
          <Space size="large">
            <Form.Item name="sso_type" label="SSO 类型">
              <Select
                style={{ width: 200 }}
                options={[
                  { value: 'token', label: 'token 跳转' },
                  { value: 'oidc', label: 'OIDC（预留）' },
                ]}
              />
            </Form.Item>
            <Form.Item name="access_mode" label="接入方式">
              <Select
                style={{ width: 200 }}
                options={[
                  { value: 'gateway', label: '经统一网关 forwardAuth' },
                  { value: 'direct', label: '直连 JWKS 自验签' },
                ]}
              />
            </Form.Item>
            <Form.Item name="sort_order" label="排序">
              <InputNumber min={0} />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </main>
  )
}
