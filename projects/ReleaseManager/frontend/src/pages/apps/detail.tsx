import { useEffect, useState } from 'react';
import {
  Card, Descriptions, Table, Button, Drawer, Form, Input, AutoComplete, Select,
  Modal, Tabs, Tag, Typography, message, Spin, Space, Divider, Steps,
} from 'antd';
import { ArrowLeftOutlined, EditOutlined, SettingOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { appApi, imageApi, userApi, authzApi, configApi } from '../../api';

const { Title, Text } = Typography;

const STATUS_OPTIONS = [
  { value: 'active', label: '启用' },
  { value: 'inactive', label: '停用' },
];

const DEPLOY_STRATEGY_LABELS: Record<string, string> = {
  rolling: '滚动更新', blue_green: '蓝绿部署', canary: '金丝雀',
};

const ENV_TYPE_ORDER = ['dev', 'test', 'staging', 'prod'];
const ENV_TYPE_LABELS: Record<string, string> = {
  dev: '开发', test: '测试', staging: '预发', prod: '生产',
};

const APPROVER_RESOLVER_LABELS: Record<string, string> = {
  app_owner: '应用负责人', group_leader: '组负责人',
  business_line_leader: '业务线负责人',
};

const TEMPLATE_TYPE_LABELS: Record<string, string> = {
  yaml: 'YAML', properties: 'Properties', env: '环境变量',
  json: 'JSON', nginx: 'Nginx', custom: '自定义',
};

// 配置模板展开行：展示该模板定义的变量在各环境的值
function ConfigTemplateVars({ template, variables, varValues }: any) {
  const vars = variables.filter((v: any) => v.template_id === template.id);
  if (vars.length === 0) {
    return <Text type="secondary">该模板未定义变量</Text>;
  }
  return (
    <Table
      size="small"
      pagination={false}
      rowKey="id"
      dataSource={vars}
      columns={[
        { title: '变量', dataIndex: 'key', width: 200, render: (v: string) => <code>{v}</code> },
        { title: '类型', dataIndex: 'value_type', width: 110, render: (v: string) => v || 'string' },
        { title: '默认值', dataIndex: 'default_value', width: 200, render: (v: string) => v || '-' },
        {
          title: '环境值', dataIndex: 'id',
          render: (vid: number) => {
            const vals = varValues.filter((vv: any) => vv.variable_id === vid);
            if (vals.length === 0) return <Text type="secondary">未配置</Text>;
            return vals.map((vv: any) => (
              <Tag key={vv.id} style={{ marginBottom: 2 }}>
                {vv.environment_name}: <code>{vv.value || '-'}</code>
              </Tag>
            ));
          },
        },
      ]}
    />
  );
}

export default function AppDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [app, setApp] = useState<any>(null);
  const [envConfigs, setEnvConfigs] = useState<any[]>([]);
  const [configTemplates, setConfigTemplates] = useState<any[]>([]);
  const [configVariables, setConfigVariables] = useState<any[]>([]);
  const [configVarValues, setConfigVarValues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 编辑 Drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  const [builderImages, setBuilderImages] = useState<string[]>([]);
  const [baseImages, setBaseImages] = useState<string[]>([]);

  // 审批流预览
  const [approvalConfig, setApprovalConfig] = useState<any>(null);
  const [approvalTemplate, setApprovalTemplate] = useState<any>(null);

  // ─── 数据加载 ──────────────────────────────────────────────

  const fetchData = () => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      appApi.detail(Number(id)),
      appApi.envConfigs.list(Number(id)),
      configApi.templates.list({ app_id: id }),
      configApi.variables.list(),
      configApi.variableValues.list(),
    ]).then(([appRes, configRes, tplRes, varRes, valRes]: any[]) => {
      setApp(appRes?.data || {});
      setEnvConfigs(configRes?.data || []);
      setConfigTemplates(tplRes?.data || []);
      setConfigVariables(varRes?.data || []);
      setConfigVarValues(valRes?.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  // ─── 打开编辑 Drawer ──────────────────────────────────────

  const openDrawer = async () => {
    // 加载用户列表
    try {
      const userRes = await userApi.list();
      setAllUsers(userRes?.data || []);
    } catch { /* ignore */ }

    // 加载镜像选项
    try {
      const imgRes = await imageApi.list();
      const list = imgRes?.data || [];
      const builders = [...new Set(list.map((r: any) => r.builder_image).filter(Boolean))];
      const bases = [...new Set(list.map((r: any) => r.base_image).filter(Boolean))];
      if (app?.builder_image && !builders.includes(app.builder_image)) builders.unshift(app.builder_image);
      if (app?.base_image && !bases.includes(app.base_image)) bases.unshift(app.base_image);
      setBuilderImages(builders);
      setBaseImages(bases);
    } catch { /* ignore */ }

    // 加载审批配置
    try {
      const cfgRes = await authzApi.appChangeApprovalConfigs.list();
      const cfgs = cfgRes?.data || [];
      if (cfgs.length > 0) {
        const cfg = cfgs[0];
        setApprovalConfig(cfg);
        if (cfg.requires_approval && cfg.flow_template) {
          const tmplRes = await authzApi.approvalFlowTemplates.detail(cfg.flow_template);
          setApprovalTemplate(tmplRes.data);
        } else {
          setApprovalTemplate(null);
        }
      }
    } catch { /* ignore */ }

    // 填充表单
    form.setFieldsValue({
      description: app?.description || '',
      repo_url: app?.repo_url || '',
      status: app?.status || 'active',
      owner_ids: app?.owner_ids || (app?.owner ? [app.owner] : []),
      builder_image: app?.builder_image || '',
      base_image: app?.base_image || '',
    });

    setDrawerOpen(true);
  };

  // ─── 提交编辑 ──────────────────────────────────────────────

  const [confirmModalVisible, setConfirmModalVisible] = useState(false);
  const [pendingValues, setPendingValues] = useState<any>(null);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (approvalConfig?.requires_approval) {
        // 需要审批：弹出确认框
        setPendingValues(values);
        setConfirmModalVisible(true);
        return;
      }
      // 无需审批：直接保存
      await doSave(values);
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error('更新失败');
    }
  };

  const doSave = async (values: any) => {
    setSubmitting(true);
    try {
      await appApi.update(Number(id), {
        description: values.description,
        repo_url: values.repo_url,
        status: values.status,
        owner_ids: values.owner_ids,
        builder_image: values.builder_image,
        base_image: values.base_image,
      });
      message.success('应用配置已更新');
      setDrawerOpen(false);
      setConfirmModalVisible(false);
      fetchData();
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error('更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── 环境配置 Tab 分组 ─────────────────────────────────────

  const envByType: Record<string, any[]> = {};
  envConfigs.forEach((cfg: any) => {
    const envType = cfg.environment_code?.replace(/\d+$/, '') || 'dev';
    if (!envByType[envType]) envByType[envType] = [];
    envByType[envType].push(cfg);
  });

  const envTabItems = ENV_TYPE_ORDER
    .filter((t) => envByType[t]?.length > 0)
    .map((envType) => ({
      key: envType,
      label: ENV_TYPE_LABELS[envType] || envType,
      children: (
        <Table dataSource={envByType[envType]} rowKey="id" size="small" pagination={false} scroll={{ x: 800 }}
          columns={[
            { title: '环境', dataIndex: 'environment_name', key: 'environment', width: 100, render: (v: string) => v || '-' },
            { title: '集群', dataIndex: 'cluster_name', key: 'cluster', width: 120, render: (v: string) => v || '-' },
            { title: '命名空间', dataIndex: 'namespace_name', key: 'namespace', width: 120, render: (v: string) => v || '-' },
            { title: '部署策略', dataIndex: 'deploy_strategy', key: 'deploy_strategy', width: 120,
              render: (v: string) => <Tag color={v === 'rolling' ? 'blue' : v === 'blue_green' ? 'purple' : 'orange'}>{DEPLOY_STRATEGY_LABELS[v] || v}</Tag> },
            { title: '副本数', dataIndex: 'replicas', key: 'replicas', width: 80, render: (v: number) => v ?? '-' },
            { title: '镜像仓库', dataIndex: 'image_repo', key: 'image_repo', width: 200, ellipsis: true, render: (v: string) => <code style={{ fontSize: 12 }}>{v || '-'}</code> },
            { title: '端口', dataIndex: 'container_port', key: 'container_port', width: 80, render: (v: number) => (v ? `${v}` : '-') },
            { title: '部署类型', dataIndex: 'environment_deploy_type', key: 'deploy_type', width: 100,
              render: (v: string) => <Tag color={v === 'k8s' ? 'blue' : 'orange'}>{v === 'k8s' ? 'K8s' : 'EC2'}</Tag> },
            {
              title: '操作', key: 'action', width: 80,
              render: (_: any, record: any) => (
                <Button type="link" size="small" icon={<SettingOutlined />}
                  onClick={() => message.info('功能开发中')}
                >编辑</Button>
              ),
            },
          ]} />
      ),
    }));

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  }

  // 负责人显示
  const ownerDisplay = (() => {
    const names = app?.owner_names;
    if (names && names.length > 0) return names.join(', ');
    return app?.owner_name || '-';
  })();

  return (
    <div>
      {/* ── 标题栏 ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          <Title level={4} style={{ margin: 0 }}>应用详情</Title>
        </Space>
        <Button type="primary" icon={<EditOutlined />} onClick={openDrawer}>编辑</Button>
      </div>

      {/* ── 基本信息 ── */}
      <Card size="small" style={{ marginBottom: 24 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="名称">{app?.name}</Descriptions.Item>
          <Descriptions.Item label="编码">{app?.code}</Descriptions.Item>
          <Descriptions.Item label="开发语言">{app?.language ? <Tag>{app.language}</Tag> : '-'}</Descriptions.Item>
          <Descriptions.Item label="业务线">{app?.business_line_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="负责人">{ownerDisplay}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={app?.status === 'active' ? 'green' : 'default'}>{app?.status === 'active' ? '启用' : app?.status || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="环境基础镜像（CI）" span={2}>
            <code style={{ fontSize: 13 }}>{app?.builder_image || '-'}</code>
          </Descriptions.Item>
          <Descriptions.Item label="应用基础镜像（CD）" span={2}>
            <code style={{ fontSize: 13 }}>{app?.base_image || '-'}</code>
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>{app?.description || '无'}</Descriptions.Item>
          <Descriptions.Item label="代码仓库" span={2}>
            {app?.repo_url ? <a href={app.repo_url} target="_blank" rel="noopener noreferrer">{app.repo_url}</a> : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{app?.created_at || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* ── 环境配置 Tab ── */}
      <Card title="环境配置" size="small" style={{ marginBottom: 24 }}>
        {envTabItems.length > 0 ? <Tabs items={envTabItems} /> : <Text type="secondary">暂无环境配置</Text>}
      </Card>

      {/* ── 配置模板（配置随发布走 · 绑定可视化） ── */}
      <Card
        title="📄 配置模板"
        size="small"
        style={{ marginBottom: 24 }}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>发布 CD 时按 应用×环境 渲染并下发 ConfigMap</Text>}
      >
        {configTemplates.length === 0 ? (
          <Text type="secondary">该应用未绑定配置模板（发布时将跳过配置下发）</Text>
        ) : (
          <Table
            dataSource={configTemplates}
            rowKey="id"
            size="small"
            pagination={false}
            columns={[
              { title: '模板名', dataIndex: 'name', key: 'name', width: 160, render: (v: string) => <Text strong>{v}</Text> },
              {
                title: '类型', dataIndex: 'template_type', key: 'type', width: 120,
                render: (v: string) => <Tag color="blue">{TEMPLATE_TYPE_LABELS[v] || v}</Tag>,
              },
              {
                title: '部署路径', dataIndex: 'deploy_path', key: 'deploy_path', width: 200,
                render: (v: string) => <code style={{ fontSize: 12 }}>{v || '-'}</code>,
              },
              { title: '版本', dataIndex: 'version', key: 'version', width: 70, render: (v: number) => `v${v}` },
              {
                title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
                render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag>,
              },
            ]}
            expandable={{
              expandedRowRender: (record: any) => (
                <ConfigTemplateVars template={record} variables={configVariables} varValues={configVarValues} />
              ),
            }}
          />
        )}
      </Card>

      {/* ══════════════════════════════════════════════════════
          编辑 Drawer
         ══════════════════════════════════════════════════════ */}
      <Drawer
        title="编辑应用配置"
        placement="right"
        width={520}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={submitting} onClick={handleSubmit}>
              提交{approvalConfig?.requires_approval ? '审批' : '保存'}
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          {/* 基本信息 */}
          <Text strong style={{ display: 'block', marginBottom: 8 }}>基本信息</Text>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="应用描述" />
          </Form.Item>
          <Form.Item name="repo_url" label="代码仓库">
            <Input placeholder="https://github.com/example/repo" />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select options={STATUS_OPTIONS} />
          </Form.Item>

          <Divider style={{ margin: '12px 0' }} />

          {/* 负责人 */}
          <Text strong style={{ display: 'block', marginBottom: 8 }}>负责人</Text>
          <Form.Item name="owner_ids" label="应用负责人">
            <Select
              mode="multiple"
              placeholder="选择负责人"
              showSearch
              optionFilterProp="label"
              options={allUsers.map((u: any) => ({
                value: u.id,
                label: `${u.display_name} (${u.username})`,
              }))}
            />
          </Form.Item>

          <Divider style={{ margin: '12px 0' }} />

          {/* 镜像配置 */}
          <Text strong style={{ display: 'block', marginBottom: 8 }}>镜像配置</Text>
          <Form.Item
            name="builder_image" label="环境基础镜像（CI 构建用）"
            rules={[{ required: true, message: '请选择或输入环境基础镜像' }]}
            tooltip="包含编译器/工具链的镜像，用于 CI 阶段的代码编译构建"
          >
            <AutoComplete
              placeholder="选择或输入"
              options={builderImages.map((img) => ({ value: img }))}
              filterOption={(inputValue, option) => option?.value.toUpperCase().includes(inputValue.toUpperCase())}
            />
          </Form.Item>
          <Form.Item
            name="base_image" label="应用基础镜像（CD 运行用）"
            rules={[{ required: true, message: '请选择或输入应用基础镜像' }]}
            tooltip="预装运行环境的镜像，产物拷贝到该镜像中组装"
          >
            <AutoComplete
              placeholder="选择或输入"
              options={baseImages.map((img) => ({ value: img }))}
              filterOption={(inputValue, option) => option?.value.toUpperCase().includes(inputValue.toUpperCase())}
            />
          </Form.Item>

          {/* 审批流预览 */}
          {approvalConfig?.requires_approval && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <Text strong style={{ display: 'block', marginBottom: 8 }}>审批流预览</Text>
              {approvalTemplate?.steps?.length > 0 ? (
                <Steps
                  direction="vertical"
                  current={-1}
                  size="small"
                  items={approvalTemplate.steps.map((step: any, idx: number) => ({
                    title: `${idx + 1}. ${step.name || '审批步骤'}`,
                    description: (
                      <div style={{ fontSize: 12 }}>
                        <div>审批人: {APPROVER_RESOLVER_LABELS[step.approver_resolver] || step.approver_resolver || '-'}</div>
                        {step.timeout_hours && <div>⏱ {step.timeout_hours} 小时内完成</div>}
                      </div>
                    ),
                  }))}
                />
              ) : (
                <Text type="secondary">需审批，但未配置审批流模板</Text>
              )}
            </>
          )}
          {approvalConfig && !approvalConfig.requires_approval && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <Text type="secondary">此变更无需审批，提交后立即生效。</Text>
            </>
          )}
        </Form>
      </Drawer>

      {/* ── 提交审批确认弹窗 ── */}
      <Modal
        title="提交审批申请"
        open={confirmModalVisible}
        onCancel={() => setConfirmModalVisible(false)}
        onOk={() => doSave(pendingValues)}
        confirmLoading={submitting}
        okText="提交审批"
        width={560}
      >
        <p>以下变更需要经过审批流程，确认提交审批申请？</p>
        {approvalTemplate?.steps?.length > 0 && (
          <Steps
            direction="vertical"
            current={-1}
            size="small"
            style={{ marginTop: 16 }}
            items={approvalTemplate.steps.map((step: any, idx: number) => ({
              title: `${idx + 1}. ${step.name || '审批步骤'}`,
              description: (
                <div style={{ fontSize: 12 }}>
                  <div>审批人: {APPROVER_RESOLVER_LABELS[step.approver_resolver] || step.approver_resolver || '-'}</div>
                  {step.timeout_hours && <div>⏱ {step.timeout_hours} 小时内完成</div>}
                </div>
              ),
            }))}
          />
        )}
        <Divider />
        <Text type="secondary">提交后，审批通过将自动更新应用配置。</Text>
      </Modal>
    </div>
  );
}