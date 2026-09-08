import { useEffect, useState } from 'react';
import {
  Typography, Table, Button, Modal, Form, Input, Select, Switch, message, Space, InputNumber,
} from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import { configApi, infraApi } from '../../api';

const { Title } = Typography;

const VALUE_TYPES = ['string', 'number', 'boolean', 'json', 'password'];

interface Template {
  id: number;
  name: string;
  app_name: string;
}

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

export default function ConfigVariablePage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | undefined>(undefined);
  const [variables, setVariables] = useState<ConfigVariable[]>([]);
  const [variableValues, setVariableValues] = useState<VariableValue[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(false);

  // Variable modal
  const [varModalOpen, setVarModalOpen] = useState(false);
  const [editingVar, setEditingVar] = useState<ConfigVariable | null>(null);
  const [varForm] = Form.useForm();

  // Value edit modal
  const [valueEditModalOpen, setValueEditModalOpen] = useState(false);
  const [editingValue, setEditingValue] = useState<VariableValue | null>(null);
  const [valueForm] = Form.useForm();

  const loadTemplates = () => {
    configApi.templates.list().then((res: any) => {
      setTemplates(res.data || []);
    });
  };

  const loadEnvironments = () => {
    infraApi.environments.list().then((res: any) => {
      // API now returns {code: 200, data: [...]}
      setEnvironments(res?.data || []);
    });
  };

  useEffect(() => {
    loadTemplates();
    loadEnvironments();
  }, []);

  useEffect(() => {
    if (!selectedTemplateId) {
      setVariables([]);
      setVariableValues([]);
      return;
    }
    setLoading(true);
    Promise.all([
      configApi.variables.list(),
      configApi.variableValues.list(),
    ]).then(([varRes, valRes]: any[]) => {
      setVariables((varRes.data || []).filter((v: ConfigVariable) => v.template_id === selectedTemplateId));
      setVariableValues(valRes.data || []);
    }).finally(() => setLoading(false));
  }, [selectedTemplateId]);

  const handleTemplateChange = (value: number) => {
    setSelectedTemplateId(value);
  };

  // Variable CRUD
  const openCreateVar = () => {
    if (!selectedTemplateId) {
      message.warning('请先选择模板');
      return;
    }
    setEditingVar(null);
    varForm.resetFields();
    varForm.setFieldsValue({ template_id: selectedTemplateId, sort_order: 0 });
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
      // Reload
      const [varRes, valRes]: any[] = await Promise.all([
        configApi.variables.list(),
        configApi.variableValues.list(),
      ]);
      setVariables((varRes.data || []).filter((v: ConfigVariable) => v.template_id === selectedTemplateId));
      setVariableValues(valRes.data || []);
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

  // Value edit
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
      // Reload values
      const valRes: any = await configApi.variableValues.list();
      setVariableValues(valRes.data || []);
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

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
          <span style={{ maxWidth: 100, display: 'inline-block', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {displayVal}
          </span>
          {val && (
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditValue(val)} />
          )}
        </Space>
      );
    },
  }));

  const varColumns = [
    { title: '变量名', dataIndex: 'key', key: 'key', width: 140 },
    { title: '类型', dataIndex: 'value_type', key: 'value_type', width: 80 },
    { title: '默认值', dataIndex: 'default_value', key: 'default_value', width: 120, ellipsis: true },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 60 },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: ConfigVariable) => (
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditVar(record)}>
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>变量管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateVar}>
          新增变量
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <span>选择模板：</span>
        <Select
          placeholder="请选择模板"
          style={{ width: 300 }}
          value={selectedTemplateId}
          onChange={handleTemplateChange}
          allowClear
          showSearch
          optionFilterProp="label"
          options={templates.map((t) => ({
            value: t.id,
            label: `${t.name} (${t.app_name})`,
          }))}
        />
      </Space>

      {selectedTemplateId && (
        <>
          <Table
            dataSource={variables}
            columns={varColumns}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={false}
            style={{ marginBottom: 16 }}
            locale={{ emptyText: '暂无变量' }}
          />

          <Title level={5} style={{ marginBottom: 8 }}>按环境变量值</Title>
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
        </>
      )}

      {!selectedTemplateId && (
        <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
          请先选择一个模板以查看变量
        </div>
      )}

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
    </div>
  );
}