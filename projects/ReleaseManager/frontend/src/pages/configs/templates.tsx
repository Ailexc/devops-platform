import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, message, Typography, Space, Tag,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { configApi, appApi } from '../../api';

const { Title } = Typography;
const { TextArea } = Input;

const TEMPLATE_TYPES = ['YAML', 'Properties', 'ENV', 'JSON', 'Nginx', '自定义'];

interface Template {
  id: number;
  app_id: number;
  app_name?: string;
  name: string;
  template_type: string;
  template_content: string;
  description: string;
  deploy_path: string;
  version: number;
  status: string;
  created_at: string;
}

export default function ConfigTemplateListPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [apps, setApps] = useState<any[]>([]);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const loadTemplates = () => {
    setLoading(true);
    configApi.templates.list().then((res: any) => {
      setTemplates(res.data || []);
    }).finally(() => setLoading(false));
  };

  const loadApps = () => {
    appApi.list().then((res: any) => {
      setApps(res.data || []);
    });
  };

  useEffect(() => {
    loadTemplates();
    loadApps();
  }, []);

  const openCreateModal = () => {
    setEditingTemplate(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEditModal = (record: Template) => {
    setEditingTemplate(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingTemplate) {
        await configApi.templates.update(editingTemplate.id, values);
        message.success('模板更新成功');
      } else {
        await configApi.templates.create(values);
        message.success('模板创建成功');
      }
      setModalOpen(false);
      loadTemplates();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('操作失败');
    }
  };

  const columns = [
    { title: '应用名', dataIndex: 'app_name', key: 'app_name', width: 140 },
    { title: '模板名称', dataIndex: 'name', key: 'name', width: 160 },
    {
      title: '类型',
      dataIndex: 'template_type',
      key: 'template_type',
      width: 100,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 70 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>{status}</Tag>
      ),
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Template) => (
        <Space>
          <Button type="link" size="small" onClick={(e) => { e.stopPropagation(); openEditModal(record); }}>
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>配置模板管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          新建模板
        </Button>
      </div>

      <Table
        dataSource={templates}
        columns={columns}
        rowKey="id"
        loading={loading}
        onRow={(record) => ({
          onClick: () => navigate(`/config/templates/${record.id}`),
          style: { cursor: 'pointer' },
        })}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
      />

      <Modal
        title={editingTemplate ? '编辑模板' : '新建模板'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        width={720}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" preserve={false}>
          <Form.Item
            name="app_id"
            label="应用"
            rules={[{ required: true, message: '请选择应用' }]}
          >
            <Select
              placeholder="请选择应用"
              showSearch
              optionFilterProp="label"
              options={apps.map((a: any) => ({ value: a.id, label: a.name }))}
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>
          <Form.Item
            name="template_type"
            label="模板类型"
            rules={[{ required: true, message: '请选择模板类型' }]}
          >
            <Select
              placeholder="请选择模板类型"
              options={TEMPLATE_TYPES.map((t) => ({ value: t, label: t }))}
            />
          </Form.Item>
          <Form.Item
            name="template_content"
            label="模板内容"
            rules={[{ required: true, message: '请输入模板内容' }]}
          >
            <TextArea rows={10} placeholder="请输入模板内容，变量使用 {{ var_name }} 语法" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item name="deploy_path" label="部署路径">
            <Input placeholder="例如 /etc/nginx/conf.d/default.conf" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}