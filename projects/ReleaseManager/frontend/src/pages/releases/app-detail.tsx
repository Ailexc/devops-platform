import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Descriptions, Tag, Button, Typography, Space, Collapse,
  Table, Select, Input, Spin, Empty, Divider, Tooltip, message, Modal,
  Tabs, Drawer, Form, Radio, Dropdown,
} from 'antd';
import {
  ArrowLeftOutlined, CaretRightOutlined,
  SendOutlined, PlusOutlined, RollbackOutlined, CopyOutlined,
  ReloadOutlined, GlobalOutlined,
  QuestionCircleOutlined, ControlOutlined,
} from '@ant-design/icons';
import { appApi, releaseApi } from '../../api';
import StateManageDrawer from '../../components/StateManageDrawer';
import TrafficManageDrawer from '../../components/TrafficManageDrawer';

const { Title, Text } = Typography;

const STATUS_COLORS: Record<string, string> = {
  pending: 'orange',
  approved: 'blue',
  running: 'cyan',
  completed: 'green',
  failed: 'red',
  rolled_back: 'purple',
  cancelled: 'default',
  rejected: 'red',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待审批',
  approved: '已审批',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  rolled_back: '已回滚',
  cancelled: '已取消',
  rejected: '已驳回',
};

const RELEASE_TYPE_LABELS: Record<string, string> = {
  regular: '常规发布',
  incremental: '增量发布',
  compensation: '补偿发布',
  rollback: '回滚发布',
  quick: '快速发布',
  scale: '实例伸缩',
  restart: '重启',
  stop: '停机',
  start: '启动',
  traffic: '流量管理',
};

const DEPLOY_STRATEGY_LABELS: Record<string, string> = {
  rolling: '滚动更新',
  blue_green: '蓝绿部署',
  canary: '金丝雀发布',
};

export default function AppReleaseDetailPage() {
  const { appId } = useParams<{ appId: string }>();
  const navigate = useNavigate();

  const [app, setApp] = useState<any>(null);
  const [envConfigs, setEnvConfigs] = useState<any[]>([]);
  const [releases, setReleases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [envFilter, setEnvFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [searchText, setSearchText] = useState('');
  const [envTab, setEnvTab] = useState('dev');

  const [rollbackModalVisible, setRollbackModalVisible] = useState(false);
  const [selectedRollbackId, setSelectedRollbackId] = useState<number | null>(null);
  const [stateDrawerOpen, setStateDrawerOpen] = useState(false);
  const [trafficDrawerOpen, setTrafficDrawerOpen] = useState(false);
  const [createDrawerOpen, setCreateDrawerOpen] = useState(false);
  const [createForm] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [editDrawerOpen, setEditDrawerOpen] = useState(false);
  const [editingRelease, setEditingRelease] = useState<any>(null);
  const [editForm] = Form.useForm();

  const fetchData = () => {
    if (!appId) return;
    setLoading(true);
    Promise.all([
      appApi.detail(Number(appId)),
      appApi.envConfigs.list(Number(appId)),
      releaseApi.list({ app: Number(appId) }),
    ]).then(([appRes, configRes, releaseRes]: any[]) => {
      // appApi.detail() returns {code: 200, data: {...}}
      // appApi.envConfigs.list() returns {code: 200, data: [...]}
      // releaseApi.list() returns {code: 200, data: [...]}
      setApp(appRes?.data || {});
      setEnvConfigs(configRes?.data || []);
      setReleases(releaseRes?.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [appId]);

  const getEnvName = (cfg: any) => {
    return cfg?.environment_name || cfg?.environment?.name || '-';
  };

  const getEnvCode = (cfg: any) => {
    return cfg?.environment_code || cfg?.environment?.code || '-';
  };

  const getClusterName = (cfg: any) => {
    return cfg?.cluster_name || cfg?.cluster?.name || '-';
  };

  const getNamespaceName = (cfg: any) => {
    return cfg?.namespace_name || cfg?.namespace?.name || '-';
  };

  const getBusinessLineName = () => {
    const bl = app?.business_line;
    if (!bl) return '-';
    return typeof bl === 'object' ? bl.name : bl;
  };

  const getOwnerName = () => {
    const owner = app?.owner;
    if (!owner) return '-';
    if (typeof owner === 'object') return owner.display_name || owner.username;
    return owner;
  };

  const handleRollback = () => {
    setSelectedRollbackId(null);
    setRollbackModalVisible(true);
  };

  const confirmRollback = () => {
    if (!selectedRollbackId || !appId) return;
    navigate(`/releases/new?appId=${appId}&mode=rollback&rollbackFrom=${selectedRollbackId}`);
    setRollbackModalVisible(false);
  };

  const handleCreateRelease = async () => {
    try {
      const values = await createForm.validateFields();
      setSubmitting(true);
      await releaseApi.create({
        application: Number(appId),
        environment: values.environment,
        title: `${app?.name || ''} ${values.version}`,
        version: values.version,
        image_tag: values.version,
        branch: values.branch || 'main',
        commit_id: values.commit_id || '',
        deploy_strategy: values.deploy_strategy || 'rolling',
        canary_percent: values.deploy_strategy === 'canary' ? 10 : 0,
      });
      message.success('发布单已创建（草稿状态）');
      setCreateDrawerOpen(false);
      createForm.resetFields();
      fetchData();
    } catch (e: any) {
      if (e?.message) message.error(String(e.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerApproval = async (id: number) => {
    try {
      await releaseApi.submitApproval(id);
      message.success('审批已提交');
      fetchData();
    } catch (e: any) {
      message.error(e?.message || '提交审批失败');
    }
  };

  const handleAutoApprove = async (id: number) => {
    try {
      await releaseApi.approveAction(id, 'approved', 'Demo 自动审批通过');
      message.success('审批已通过');
      fetchData();
    } catch (e: any) {
      message.error(e?.message || '审批操作失败');
    }
  };

  const handleExecuteRelease = async (id: number) => {
    try {
      await releaseApi.execute(id);
      message.success('发布已触发，CI 构建开始');
      navigate(`/releases/${id}`);
    } catch (e: any) {
      message.error(e?.message || '触发发布失败');
    }
  };

  const handleEditRelease = async () => {
    if (!editingRelease) return;
    try {
      const values = await editForm.validateFields();
      setSubmitting(true);
      await releaseApi.update(editingRelease.id, {
        version: values.version,
        image_tag: values.version,
        branch: values.branch,
        commit_id: values.commit_id,
        deploy_strategy: values.deploy_strategy,
      });
      message.success('发布单已更新');
      setEditDrawerOpen(false);
      setEditingRelease(null);
      fetchData();
    } catch (e: any) {
      if (e?.message) message.error(String(e.message));
    } finally {
      setSubmitting(false);
    }
  };

  const getLastReleaseId = () => {
    if (releases.length === 0) return null;
    return releases[0].id;
  };

  const rollbackCandidates = releases
    .filter((r: any) => r.status === 'completed' || r.status === 'rolled_back')
    .slice(0, 10);

  const filteredReleases = releases.filter((r: any) => {
    if (envFilter) {
      const envName = typeof r.env_config === 'object'
        ? (r.env_config?.environment_name || r.env_config?.environment?.name || '')
        : '';
      if (envName !== envFilter) return false;
    }
    if (statusFilter && r.status !== statusFilter) return false;
    if (typeFilter && r.release_mode !== typeFilter) return false;
    if (searchText && r.release_no && !r.release_no.toLowerCase().includes(searchText.toLowerCase())) return false;
    return true;
  });

  const envOptions = envConfigs.map((cfg: any) => ({
    value: getEnvName(cfg),
    label: getEnvName(cfg),
  }));

  const statusOptions = [
    { value: '', label: '全部' },
    { value: 'pending', label: '待审批' },
    { value: 'approved', label: '已审批' },
    { value: 'running', label: '运行中' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '失败' },
    { value: 'rolled_back', label: '已回滚' },
    { value: 'cancelled', label: '已取消' },
  ];

  const typeOptions = [
    { value: '', label: '全部' },
    { value: 'regular', label: '常规发布' },
    { value: 'incremental', label: '增量发布' },
    { value: 'compensation', label: '补偿发布' },
    { value: 'rollback', label: '回滚发布' },
    { value: 'quick', label: '快速发布' },
    { value: 'scale', label: '实例伸缩' },
    { value: 'restart', label: '重启' },
    { value: 'stop', label: '停机' },
    { value: 'start', label: '启动' },
    { value: 'traffic', label: '流量管理' },
  ];

  const historyColumns = [
    {
      title: '类型', key: 'release_mode', width: 90,
      render: (_: any, r: any) => (
        <Tag color={r.release_mode === 'scale' ? 'geekblue' : 'blue'}>
          {RELEASE_TYPE_LABELS[r.release_mode] || '常规发布'}
        </Tag>
      ),
    },
    {
      title: '发布单号', dataIndex: 'release_no', key: 'release_no', width: 160,
      render: (v: string) => <Typography.Text code>{v}</Typography.Text>,
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 100,
      render: (v: string, r: any) => {
        if (r.release_mode === 'scale') return <Text type="secondary">{`${r.current_replicas ?? '?'} → ${r.target_replicas ?? '?'}`}</Text>;
        if (r.release_mode === 'restart') return <Text type="secondary">滚动重启</Text>;
        if (r.release_mode === 'stop') return <Text type="secondary">缩容到 0</Text>;
        if (r.release_mode === 'start') return <Text type="secondary">恢复副本</Text>;
        if (r.release_mode === 'traffic') return <Text type="secondary">{r.traffic_action === 'take_out' ? '摘流' : r.traffic_action === 'restore' ? '挂流' : '流量'}</Text>;
        return v;
      },
    },
    {
      title: '环境', key: 'environment', width: 100,
      render: (_: any, r: any) => {
        const name = r.environment_name || '-';
        const code = r.environment_code || '';
        const colorMap: Record<string, string> = { dev: 'blue', test: 'green', staging: 'orange', prod: 'red' };
        return <Tag color={colorMap[code] || 'default'}>{name}</Tag>;
      },
    },
    {
      title: 'CI', key: 'ci', width: 80,
      render: (_: any, r: any) => {
        const ci = (r.tasks || []).find((t: any) => t.stage === 'ci');
        if (!ci) return <Tag>—</Tag>;
        const m: Record<string, { c: string; t: string }> = {
          pending: { c: 'default', t: '等待' }, running: { c: 'processing', t: '构建中' },
          success: { c: 'success', t: '✅' }, failed: { c: 'error', t: '❌' },
        };
        const cfg = m[ci.status] || m.pending;
        return <Tag color={cfg.c}>{cfg.t}</Tag>;
      },
    },
    {
      title: 'CD', key: 'cd', width: 80,
      render: (_: any, r: any) => {
        const cd = (r.tasks || []).find((t: any) => t.stage === 'cd');
        if (!cd) return <Tag>—</Tag>;
        const m: Record<string, { c: string; t: string }> = {
          pending: { c: 'default', t: '等待' }, running: { c: 'processing', t: '部署中' },
          success: { c: 'success', t: '✅' }, failed: { c: 'error', t: '❌' },
        };
        const cfg = m[cd.status] || m.pending;
        return <Tag color={cfg.c}>{cfg.t}</Tag>;
      },
    },
    {
      title: '审批状态', dataIndex: 'approval_status', key: 'approval_status', width: 100,
      render: (v: string, r: any) => {
        const m: Record<string, { c: string; t: string }> = {
          not_submitted: { c: 'default', t: '未发起' },
          submitting: { c: 'processing', t: '审批中' },
          passed: { c: 'success', t: '已通过' },
          rejected: { c: 'error', t: '已驳回' },
          not_needed: { c: 'default', t: '无需审批' },
        };
        const cfg = m[v] || m.not_submitted;
        return <Tag color={cfg.c}>{cfg.t}</Tag>;
      },
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v: string, record: any) => {
        const labels: Record<string, string> = {
          draft: '草稿', pending: '审批中', approved: '已审批', running: '发布中',
          completed: '已完成', failed: '失败', rolled_back: '已回滚', cancelled: '已取消', rejected: '已驳回',
        };
        const colors: Record<string, string> = {
          draft: 'default', pending: 'orange', approved: 'blue', running: 'cyan',
          completed: 'green', failed: 'red', rolled_back: 'purple', cancelled: 'default', rejected: 'red',
        };
        let label = labels[v] || v;
        if (v === 'failed') {
          if (record.ci_status === 'failed') label = 'CI失败';
          else if (record.cd_status === 'failed') label = 'CD失败';
        }
        return <Tag color={colors[v] || 'default'}>{label}</Tag>;
      },
    },
    {
      title: '策略', dataIndex: 'deploy_strategy', key: 'strategy', width: 80,
      render: (v: string) => {
        const labels: Record<string, string> = { rolling: '滚动', canary: '灰度', blue_green: '蓝绿' };
        return <Tag>{labels[v] || v || '-'}</Tag>;
      },
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 155 },
    {
      title: '操作', key: 'action', width: 80, fixed: 'right' as const,
      render: (_: any, record: any) => {
        const canSubmit = record.need_approval && record.approval_status === 'not_submitted';
        const canApprove = record.need_approval && record.approval_status === 'submitting';
        const canExecute = (!record.need_approval && record.status === 'draft')
          || record.approval_status === 'passed';
        const canEdit = record.status === 'draft';
        return (
          <Dropdown menu={{
            items: [
              { key: 'view', label: '查看详情', onClick: () => navigate(`/releases/${record.id}`) },
              { key: 'clone', label: '克隆',
                onClick: () => navigate(`/releases/new?appId=${appId}&cloneFrom=${record.id}`) },
              { key: 'submit', label: '发起审批', disabled: !canSubmit,
                onClick: () => handleTriggerApproval(record.id) },
              { key: 'approve', label: '模拟审批通过', disabled: !canApprove,
                onClick: () => handleAutoApprove(record.id) },
              { key: 'execute', label: '发布', disabled: !canExecute,
                onClick: () => handleExecuteRelease(record.id) },
              { key: 'edit', label: '编辑', disabled: !canEdit,
                onClick: () => { setEditingRelease(record); setEditDrawerOpen(true); } },
            ],
          }} trigger={['click']}>
            <Button type="link" size="small">操作 ▾</Button>
          </Dropdown>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!app) {
    return <Empty description="应用不存在" />;
  }

  return (
    <div>
      {/* 页面顶部 */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>{app.name}</Title>
        {app.language && <Tag>{app.language}</Tag>}
        {app.deploy_mode && <Tag color="blue">{app.deploy_mode}</Tag>}
      </div>

      {/* 主内容区 */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        {/* 左侧 - 应用信息区 70% */}
        <div style={{ flex: 7 }}>
          {/* 基础属性 */}
          <Card title="基础属性" size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="名称">{app.name}</Descriptions.Item>
              <Descriptions.Item label="编码">{app.code || '-'}</Descriptions.Item>
              <Descriptions.Item label="代码仓库">
                {app.repo_url ? (
                  <a href={app.repo_url} target="_blank" rel="noopener noreferrer">{app.repo_url}</a>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="开发语言">
                {app.language ? <Tag>{app.language}</Tag> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="业务线">{getBusinessLineName()}</Descriptions.Item>
              <Descriptions.Item label="负责人">{getOwnerName()}</Descriptions.Item>
              {app.description && (
                <Descriptions.Item label="描述" span={2}>{app.description}</Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* 环境配置 */}
          <Card
            title="环境配置"
            size="small"
            style={{ marginBottom: 16, height: 420 }}
            styles={{ body: { maxHeight: 340, overflowY: 'auto' } }}
            extra={<Text type="secondary">共 {envConfigs.length} 个环境</Text>}
          >
            {envConfigs.length === 0 ? (
              <Empty description="暂无环境配置" />
            ) : (
              (() => {
                const groupedEnvs: Record<string, any[]> = {
                  dev: envConfigs.filter((c: any) => getEnvCode(c).startsWith('dev')),
                  test: envConfigs.filter((c: any) => getEnvCode(c).startsWith('test')),
                  pre: envConfigs.filter((c: any) => getEnvCode(c).startsWith('pre')),
                  prod: envConfigs.filter((c: any) => getEnvCode(c).startsWith('prod')),
                };
                const currentEnvs = groupedEnvs[envTab] || [];

                return (
                  <>
                    <Tabs
                      activeKey={envTab}
                      onChange={setEnvTab}
                      size="small"
                      style={{ marginBottom: 12 }}
                      items={[
                        { key: 'dev', label: `dev (${groupedEnvs.dev.length})` },
                        { key: 'test', label: `test (${groupedEnvs.test.length})` },
                        { key: 'pre', label: `pre (${groupedEnvs.pre.length})` },
                        { key: 'prod', label: `prod (${groupedEnvs.prod.length})` },
                      ]}
                    />
                    {currentEnvs.length === 0 ? (
                      <Empty description="该环境分组暂无配置" />
                    ) : (
                      <Collapse
                        defaultActiveKey={[String(currentEnvs[0]?.id)]}
                        expandIcon={({ isActive }) => (
                          <CaretRightOutlined rotate={isActive ? 90 : 0} />
                        )}
                        style={{ background: '#fff' }}
                        items={currentEnvs.map((cfg: any) => ({
                          key: String(cfg.id),
                          label: <Text strong>{getEnvName(cfg)}</Text>,
                          children: (
                            <Descriptions column={2} size="small">
                              <Descriptions.Item label="集群">{getClusterName(cfg)}</Descriptions.Item>
                              <Descriptions.Item label="命名空间">{getNamespaceName(cfg)}</Descriptions.Item>
                              <Descriptions.Item label="副本数">{cfg.replicas ?? '-'}</Descriptions.Item>
                              <Descriptions.Item label="部署策略">
                                <Tag color={cfg.deploy_strategy === 'rolling' ? 'blue' : cfg.deploy_strategy === 'blue_green' ? 'purple' : 'orange'}>
                                  {DEPLOY_STRATEGY_LABELS[cfg.deploy_strategy] || cfg.deploy_strategy || '-'}
                                </Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="镜像仓库">{cfg.image_repo || '-'}</Descriptions.Item>
                              <Descriptions.Item label="容器端口">{cfg.container_port ?? '-'}</Descriptions.Item>
                              <Descriptions.Item label="CPU限制">{cfg.cpu_limit || '-'}</Descriptions.Item>
                              <Descriptions.Item label="内存限制">{cfg.memory_limit || '-'}</Descriptions.Item>
                              <Descriptions.Item label="健康检查路径">{cfg.health_check_path || '-'}</Descriptions.Item>
                              <Descriptions.Item label="自动回滚">
                                <Tag color={cfg.auto_rollback ? 'green' : 'default'}>
                                  {cfg.auto_rollback ? '启用' : '禁用'}
                                </Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="健康检查超时">
                                {cfg.health_check_timeout ? `${cfg.health_check_timeout}秒` : '-'}
                              </Descriptions.Item>
                              {cfg.config_template && (
                                <Descriptions.Item label="绑定配置模板" span={2}>
                                  {typeof cfg.config_template === 'object' ? cfg.config_template.name : cfg.config_template}
                                </Descriptions.Item>
                              )}
                            </Descriptions>
                          ),
                        }))}
                      />
                    )}
                  </>
                );
              })()
            )}
          </Card>
        </div>

        {/* 右侧 - 操作面板 30% */}
        <div style={{ flex: 3 }}>
          <Card size="small" styles={{ body: { padding: '12px 16px' } }}>
            <Space orientation="vertical" style={{ width: '100%' }} size="small">
              <Text strong style={{ color: '#1677ff' }}>🚀 创建发布</Text>

              <Tooltip title="创建一条新的常规发布申请。选择分支/Commit，填写版本号，提交后进入审批-发布流水线。真实Spug中的默认发布方式。">
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  size="large"
                  block
                  onClick={() => navigate(`/releases/new?appId=${appId}&mode=regular`)}
                >
                  常规发布 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Tooltip title="仅对未部署过当前版本的目标机器/Pod进行部署。适用于分批发布场景，只部署新增或变更的目标。">
                <Button
                  icon={<PlusOutlined />}
                  size="large"
                  block
                  onClick={() => navigate(`/releases/new?appId=${appId}&mode=incremental`)}
                >
                  增量发布 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Tooltip title="仅对上一次发布失败的目标进行重试。适用于部分目标发布失败后的修复场景。">
                <Button
                  icon={<ReloadOutlined />}
                  size="large"
                  block
                  onClick={() => navigate(`/releases/new?appId=${appId}&mode=compensation`)}
                >
                  补偿发布 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Tooltip title="基于历史发布记录创建回滚发布单。真实系统中会创建新发布单，release_mode=rollback，rollback_from关联原发布单。">
                <Button
                  icon={<RollbackOutlined />}
                  size="large"
                  block
                  onClick={handleRollback}
                >
                  回滚 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Tooltip title="快速复制最近一条发布记录的配置（分支、版本、环境等），可修改部分参数后提交。">
                <Button
                  icon={<CopyOutlined />}
                  size="large"
                  block
                  disabled={!getLastReleaseId()}
                  onClick={() => {
                    const lastId = getLastReleaseId();
                    if (lastId) navigate(`/releases/new?appId=${appId}&cloneFrom=${lastId}`);
                  }}
                >
                  克隆 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Divider style={{ margin: '8px 0' }} />

              <Text strong style={{ color: '#722ed1' }}>🛠 运行管理</Text>

              <Tooltip title="对当前环境执行运行时状态变更：重启 / 停机 / 启动 / 实例伸缩。按环境选择操作，K8s 与 EC2 走不同执行方式。">
                <Button
                  icon={<ControlOutlined />}
                  size="large"
                  block
                  onClick={() => setStateDrawerOpen(true)}
                >
                  状态管理 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>

              <Tooltip title="摘流/挂流：将服务从流量中摘除或恢复。K8s 修改 Service Selector；EC2 通过 ALB Target Group deregister/register。">
                <Button
                  icon={<GlobalOutlined />}
                  size="large"
                  block
                  onClick={() => setTrafficDrawerOpen(true)}
                >
                  流量管理 <QuestionCircleOutlined style={{ fontSize: 12, marginLeft: 4 }} />
                </Button>
              </Tooltip>
            </Space>
          </Card>
        </div>
      </div>

      {/* 底部 - 发布历史 */}
      <Card
        title="📜 发布历史"
        size="small"
      >
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <Select
            allowClear
            placeholder="环境"
            style={{ width: 120 }}
            value={envFilter}
            onChange={(val) => setEnvFilter(val)}
            options={envOptions}
          />
          <Select
            allowClear
            placeholder="状态"
            style={{ width: 120 }}
            value={statusFilter}
            onChange={(val) => setStatusFilter(val)}
            options={statusOptions}
          />
          <Select
            allowClear
            placeholder="类型"
            style={{ width: 120 }}
            value={typeFilter}
            onChange={(val) => setTypeFilter(val)}
            options={typeOptions}
          />
          <Input.Search
            allowClear
            placeholder="搜索发布单号"
            style={{ width: 200 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={(val) => setSearchText(val)}
          />
        </div>

        <Table
          dataSource={filteredReleases}
          columns={historyColumns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
          scroll={{ x: 840 }}
          locale={{ emptyText: '暂无发布历史' }}
        />
      </Card>

      {/* 回滚弹窗 */}
      <Modal
        title="选择回滚版本"
        open={rollbackModalVisible}
        onOk={confirmRollback}
        onCancel={() => setRollbackModalVisible(false)}
        okButtonProps={{ disabled: !selectedRollbackId }}
        width={640}
        destroyOnHidden
      >
        {rollbackCandidates.length === 0 ? (
          <Empty description="暂无可用于回滚的发布记录" />
        ) : (
          <Table
            dataSource={rollbackCandidates}
            rowKey="id"
            size="small"
            pagination={false}
            rowSelection={{
              type: 'radio',
              selectedRowKeys: selectedRollbackId ? [selectedRollbackId] : [],
              onChange: (keys) => setSelectedRollbackId(keys[0] as number),
            }}
            columns={[
              { title: '发布单号', dataIndex: 'release_no', key: 'release_no', width: 160 },
              { title: '版本', dataIndex: 'version', key: 'version', width: 120 },
              {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                width: 100,
                render: (v: string) => (
                  <Tag color={STATUS_COLORS[v] || 'default'}>{STATUS_LABELS[v] || v}</Tag>
                ),
              },
              { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
            ]}
          />
        )}
      </Modal>

      {/* 新建发布抽屉 */}
      <Drawer title="新建发布" open={createDrawerOpen} onClose={() => setCreateDrawerOpen(false)} size="default"
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button onClick={() => setCreateDrawerOpen(false)} style={{ marginRight: 8 }}>取消</Button>
            <Button type="primary" loading={submitting} onClick={handleCreateRelease}>提交发布</Button>
          </div>
        }>
        <Form form={createForm} layout="vertical">
          <Form.Item label="应用"><Input value={app?.name} disabled /></Form.Item>
          <Form.Item name="environment" label="目标环境" rules={[{ required: true, message: '请选择环境' }]}>
            <Select placeholder="选择环境" options={[
              { label: 'Dev 开发环境', value: 2 },
              { label: 'Test 测试环境', value: 3 },
              { label: 'Staging 预发环境', value: 4 },
              { label: 'Prod 生产环境', value: 5 },
            ]} />
          </Form.Item>
          <Form.Item name="branch" label="分支" initialValue={app?.repo_branch || 'main'}>
            <Select options={[
              { label: 'main', value: 'main' }, { label: 'develop', value: 'develop' },
              { label: 'release/v1.2', value: 'release/v1.2' },
            ]} />
          </Form.Item>
          <Form.Item name="commit_id" label="Commit ID" initialValue="abc1234">
            <Input placeholder="abc1234" />
          </Form.Item>
          <Form.Item name="version" label="版本号" rules={[{ required: true, message: '请输入版本号' }]}>
            <Input placeholder="1.2.1" />
          </Form.Item>
          <Form.Item name="deploy_strategy" label="部署策略" initialValue="rolling">
            <Radio.Group>
              <Radio.Button value="rolling">滚动更新</Radio.Button>
              <Radio.Button value="canary">灰度发布</Radio.Button>
              <Radio.Button value="blue_green">蓝绿部署</Radio.Button>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Drawer>

      {/* 编辑发布抽屉 */}
      <Drawer title="编辑发布单" open={editDrawerOpen}
        onClose={() => { setEditDrawerOpen(false); setEditingRelease(null); }} size="default"
        footer={
          <div style={{ textAlign: 'right' }}>
            <Button onClick={() => setEditDrawerOpen(false)} style={{ marginRight: 8 }}>取消</Button>
            <Button type="primary" loading={submitting} onClick={handleEditRelease}>保存</Button>
          </div>
        }>
        <Form form={editForm} layout="vertical" initialValues={{
          version: editingRelease?.version,
          branch: editingRelease?.branch || 'main',
          commit_id: editingRelease?.commit_id || '',
          deploy_strategy: editingRelease?.deploy_strategy || 'rolling',
        }}>
          <Form.Item name="version" label="版本号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="branch" label="分支"><Input /></Form.Item>
          <Form.Item name="commit_id" label="Commit ID"><Input /></Form.Item>
          <Form.Item name="deploy_strategy" label="部署策略">
            <Radio.Group>
              <Radio.Button value="rolling">滚动更新</Radio.Button>
              <Radio.Button value="canary">灰度发布</Radio.Button>
              <Radio.Button value="blue_green">蓝绿部署</Radio.Button>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Drawer>

      {/* 状态管理抽屉 */}
      <StateManageDrawer
        open={stateDrawerOpen}
        onClose={() => setStateDrawerOpen(false)}
        appId={Number(appId)}
        appName={app?.name || ''}
        envConfigs={envConfigs}
        onSuccess={fetchData}
      />

      {/* 流量管理抽屉 */}
      <TrafficManageDrawer
        open={trafficDrawerOpen}
        onClose={() => setTrafficDrawerOpen(false)}
        appId={Number(appId)}
        appName={app?.name || ''}
        envConfigs={envConfigs}
        onSuccess={fetchData}
      />
    </div>
  );
}