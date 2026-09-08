import { useEffect, useState } from 'react';
import {
  Typography, Descriptions, Table, Button, Modal, Form, Input, Select, Switch, message,
  Space, Tag, Card, Spin, InputNumber, Tooltip,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { configApi, infraApi } from '../../api';

const { Text } = Typography;
const { TextArea } = Input;

const VALUE_TYPES = ['string', 'number', 'boolean', 'json', 'password'];

interface ConfigVariable {
  id: number;
  template_id: number;
  key: string;
  value_type: string;
  default_value: string;
  description: string;
  is_secret: boolean;
  is_required: boolean;
  sort_order: number;
}

interface VariableValue {
  id: number;
  variable_id: number;
  environment_id: number;
  environment_name?: string;
  value: string;
}

interface Environment {
  id: number;
  name: string;
  code: string;
}

export default function ConfigTemplateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const templateId = Number(id);

  const [template, setTemplate] = useState<any>(null);
  const [variables, setVariables] = useState<ConfigVariable[]>([]);
  const [variableValues, setVariableValues] = useState<VariableValue[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(true);

  // Variable modal
  const [varModalOpen, setVarModalOpen] = useState(false);
  const [editingVar, setEditingVar] = useState<ConfigVariable | null>(null);
  const [varForm] = Form.useForm();

  // Value edit modal
  const [valueEditModalOpen, setValueEditModalOpen] = useState(false);
  const [editingValue, setEditingValue] = useState<VariableValue | null>(null);
  const [valueForm] = Form.useForm();

  // Render preview
  const [renderEnv, setRenderEnv] = useState<number | undefined>(undefined);
  const [renderResult, setRenderResult] = useState('');
  const [renderLoading, setRenderLoading] = useState(false);

  // Edit template modal
  const [editTemplateModalOpen, setEditTemplateModalOpen] = useState(false);
  const [templateForm] = Form.useForm();

  const loadData = () => {
    setLoading(true);
    Promise.all([
      configApi.templates.detail(templateId),
      configApi.variables.list(),
      configApi.variableValues.list(),
      infraApi.environments.list(),
    ]).then(([templateRes, varRes, valRes, envRes]: any[]) => {
      setTemplate(templateRes.data || templateRes);
      const allVars = (varRes.data || []).filter((v: ConfigVariable) => v.template_id === templateId);
      setVariables(allVars);
      setVariableValues(valRes.data || []);
      setEnvironments(envRes?.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [templateId]);

  // Variable CRUD
  const openCreateVar = () => {
    setEditingVar(null);
    varForm.resetFields();
    varForm.setFieldsValue({ template_id: templateId, sort_order: 0 });
    setVarModalOpen(true);
  };

  const openEditVar = (record: ConfigVariable) => {
    setEditingVar(record);
    varForm.setFieldsValue(record);
    setVarModalOpen(true);
  };

  const handleVarSubmit = async () => {
    try {
      const values = await varForm.validateFields();
      if (editingVar) {
        await configApi.variables.update(editingVar.id, values);
        message.success('变量更新成功');
      } else {
        await configApi.variables.create(values);
        message.success('变量创建成功');
      }
      setVarModalOpen(false);
      loadData();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

  const handleDeleteVar = (record: ConfigVariable) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除变量 "${record.key}" 吗？`,
      onOk: async () => {
        try {
          await configApi.variables.update(record.id, { is_deleted: true });
          message.success('删除成功');
          loadData();
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  // Value CRUD
  const openEditValue = (value: VariableValue) => {
    setEditingValue(value);
    valueForm.setFieldsValue({ value: value.value });
    setValueEditModalOpen(true);
  };

  const handleValueSubmit = async () => {
    try {
      const values = await valueForm.validateFields();
      if (editingValue) {
        await configApi.variableValues.update(editingValue.id, values);
        message.success('值更新成功');
      }
      setValueEditModalOpen(false);
      loadData();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

  // Render preview
  const handleRender = async () => {
    if (!renderEnv) {
      message.warning('请先选择环境');
      return;
    }
    setRenderLoading(true);
    try {
      const res: any = await configApi.templates.render(templateId, { environment_id: renderEnv });
      setRenderResult(res.data?.rendered_content || res.rendered_content || '');
    } catch {
      message.error('渲染失败');
    } finally {
      setRenderLoading(false);
    }
  };

  // Publish release
  const handlePublish = async () => {
    if (!renderEnv) {
      message.warning('请先选择渲染环境');
      return;
    }
    try {
      const res: any = await configApi.templates.render(templateId, { environment_id: renderEnv });
      const renderedContent = res.data?.rendered_content || res.rendered_content || '';
      await configApi.releases.create({
        template_id: templateId,
        environment_id: renderEnv,
        rendered_content: renderedContent,
      });
      message.success('配置发布成功');
    } catch {
      message.error('发布失败');
    }
  };

  // Edit template
  const openEditTemplate = () => {
    templateForm.setFieldsValue(template);
    setEditTemplateModalOpen(true);
  };

  const handleEditTemplate = async () => {
    try {
      const values = await templateForm.validateFields();
      await configApi.templates.update(templateId, values);
      message.success('模板更新成功');
      setEditTemplateModalOpen(false);
      loadData();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

  if (loading) {
    return <Spin style={{ display: 'block', marginTop: 100 }} />;
  }

  // Build value matrix: rows = variables, cols = environments
  const getValue = (variableId: number, envId: number): VariableValue | undefined => {
    return variableValues.find((v) => v.variable_id === variableId && v.environment_id === envId);
  };

  const envColumns = environments.map((env) => ({
    title: env.name,
    key: `env_${env.id}`,
    width: 150,
    render: (_: any, record: ConfigVariable) => {
      const val = getValue(record.id, env.id);
      const displayVal = record.is_secret && val?.value ? '******' : (val?.value || '-');
      return (
        <Space>
          <Text
            style={{ maxWidth: 100, display: 'inline-block', overflow: 'hidden', textOverflow: 'ellipsis' }}
            ellipsis={{ tooltip: val?.value }}
          >
            {displayVal}
          </Text>
          {val && (
            <Tooltip title="编辑">
              <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditValue(val)} />
            </Tooltip>
          )}
        </Space>
      );
    },
  }));

  const varColumns = [
    { title: '变量名', dataIndex: 'key', key: 'key', width: 140 },
    { title: '类型', dataIndex: 'value_type', key: 'value_type', width: 80 },
    { title: '默认值', dataIndex: 'default_value', key: 'default_value', width: 120, ellipsis: true },
    {
      title: '是否必填',
      dataIndex: 'is_required',
      key: 'is_required',
      width: 80,
      render: (v: boolean) => v ? <Tag color="red">是</Tag> : <Tag>否</Tag>,
    },
    {
      title: '是否敏感',
      dataIndex: 'is_secret',
      key: 'is_secret',
      width: 80,
      render: (v: boolean) => v ? <Tag color="orange">是</Tag> : <Tag>否</Tag>,
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: ConfigVariable) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditVar(record)}>
            编辑
          </Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteVar(record)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/config/templates')}>返回</Button>
      </Space>

      {/* Template info */}
      <Card
        title="模板信息"
        size="small"
        extra={<Button size="small" icon={<EditOutlined />} onClick={openEditTemplate}>编辑</Button>}
        style={{ marginBottom: 16 }}
      >
        <Descriptions column={3} size="small">
          <Descriptions.Item label="模板名称">{template?.name}</Descriptions.Item>
          <Descriptions.Item label="类型"><Tag>{template?.template_type}</Tag></Descriptions.Item>
          <Descriptions.Item label="版本">{template?.version}</Descriptions.Item>
          <Descriptions.Item label="描述" span={3}>{template?.description || '-'}</Descriptions.Item>
          <Descriptions.Item label="部署路径" span={3}>{template?.deploy_path || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态" span={3}>
            <Tag color={template?.status === 'active' ? 'green' : 'default'}>{template?.status}</Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Variables */}
      <Card
        title="变量管理"
        size="small"
        extra={<Button type="primary" size="small" icon={<PlusOutlined />} onClick={openCreateVar}>新增变量</Button>}
        style={{ marginBottom: 16 }}
      >
        <Table
          dataSource={variables}
          columns={varColumns}
          rowKey="id"
          size="small"
          pagination={false}
          locale={{ emptyText: '暂无变量，请新增变量' }}
        />
      </Card>

      {/* Variable values per environment */}
      <Card title="值管理" size="small" style={{ marginBottom: 16 }}>
        <Table
          dataSource={variables}
          columns={[
            { title: '变量名', dataIndex: 'key', key: 'key', width: 140, fixed: 'left' },
            ...envColumns,
          ]}
          rowKey="id"
          size="small"
          pagination={false}
          scroll={{ x: 'max-content' }}
          locale={{ emptyText: '暂无变量数据' }}
        />
      </Card>

      {/* Render preview & publish */}
      <Card title="渲染预览" size="small" style={{ marginBottom: 16 }}>
        <Space orientation="vertical" style={{ width: '100%' }}>
          <Space>
            <Select
              placeholder="请选择环境"
              style={{ width: 200 }}
              value={renderEnv}
              onChange={setRenderEnv}
              options={environments.map((e) => ({ value: e.id, label: e.name }))}
            />
            <Button type="primary" onClick={handleRender} loading={renderLoading}>渲染</Button>
            <Button type="primary" ghost onClick={handlePublish} disabled={!renderEnv}>发布配置</Button>
          </Space>
          {renderResult && (
            <TextArea
              value={renderResult}
              readOnly
              rows={12}
              style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 8 }}
            />
          )}
        </Space>
      </Card>

      {/* Variable modal */}
      <Modal
        title={editingVar ? '编辑变量' : '新增变量'}
        open={varModalOpen}
        onCancel={() => setVarModalOpen(false)}
        onOk={handleVarSubmit}
        destroyOnHidden
      >
        <Form form={varForm} layout="vertical" preserve={false}>
          <Form.Item name="template_id" hidden><Input /></Form.Item>
          <Form.Item
            name="key"
            label="变量名"
            rules={[{ required: true, message: '请输入变量名' }]}
          >
            <Input placeholder="例如：server_port" />
          </Form.Item>
          <Form.Item
            name="value_type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select options={VALUE_TYPES.map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item name="default_value" label="默认值">
            <Input placeholder="默认值" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input placeholder="变量描述" />
          </Form.Item>
          <Form.Item name="is_secret" label="是否敏感" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_required" label="是否必填" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Value edit modal */}
      <Modal
        title="编辑变量值"
        open={valueEditModalOpen}
        onCancel={() => setValueEditModalOpen(false)}
        onOk={handleValueSubmit}
        destroyOnHidden
      >
        <Form form={valueForm} layout="vertical" preserve={false}>
          <Form.Item
            name="value"
            label="值"
            rules={[{ required: true, message: '请输入值' }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit template modal */}
      <Modal
        title="编辑模板"
        open={editTemplateModalOpen}
        onCancel={() => setEditTemplateModalOpen(false)}
        onOk={handleEditTemplate}
        width={720}
        destroyOnHidden
      >
        <Form form={templateForm} layout="vertical" preserve={false}>
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="template_type"
            label="模板类型"
            rules={[{ required: true, message: '请选择模板类型' }]}
          >
            <Select options={['YAML', 'Properties', 'ENV', 'JSON', 'Nginx', '自定义'].map((t) => ({ value: t, label: t }))} />
          </Form.Item>
          <Form.Item
            name="template_content"
            label="模板内容"
            rules={[{ required: true, message: '请输入模板内容' }]}
          >
            <TextArea rows={10} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="deploy_path" label="部署路径">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}