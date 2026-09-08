import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Tag, Space, Typography, message,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { appApi, userApi, orgApi } from '../../api';

const { Title } = Typography;

const LANGUAGE_OPTIONS = [
  { value: 'Python', label: 'Python' },
  { value: 'Go', label: 'Go' },
  { value: 'Node.js', label: 'Node.js' },
  { value: 'Java', label: 'Java' },
  { value: '其他', label: '其他' },
];

const STATUS_COLORS: Record<string, string> = {
  active: 'green',
  inactive: 'default',
  archived: 'orange',
};

const STATUS_LABELS: Record<string, string> = {
  active: '启用',
  inactive: '停用',
  archived: '归档',
};

export default function AppListPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [businessLines, setBusinessLines] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingApp, setEditingApp] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchApps = () => {
    setLoading(true);
    appApi.list().then((res: any) => {
      // appApi.list() returns {code: 200, data: [...]}
      setApps(res?.data || []);
    }).finally(() => setLoading(false));
  };

  const fetchFormData = () => {
    Promise.all([
      orgApi.businessLines.list(),
      userApi.list(),
    ]).then(([blRes, userRes]: any[]) => {
      // APIs return {code: 200, data: [...]}
      setBusinessLines(blRes?.data || []);
      setUsers(userRes?.data || []);
    });
  };

  useEffect(() => {
    fetchApps();
  }, []);

  const openCreateModal = () => {
    fetchFormData();
    setEditingApp(null);
    form.resetFields();
    form.setFieldsValue({ language: 'Python', status: 'active' });
    setModalVisible(true);
  };

  const openEditModal = (record: any) => {
    fetchFormData();
    setEditingApp(record);
    form.setFieldsValue({
      name: record.name,
      code: record.code,
      description: record.description,
      language: record.language,
      repo_url: record.repo_url,
      business_line: record.business_line_id ?? record.business_line?.id,
      owner: record.owner_id ?? record.owner?.id,
      status: record.status,
    });
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingApp) {
        await appApi.update(editingApp.id, values);
        message.success('应用更新成功');
      } else {
        await appApi.create(values);
        message.success('应用创建成功');
      }
      setModalVisible(false);
      fetchApps();
    } catch (err: any) {
      if (err?.errorFields) return; // 表单验证失败
      message.error(editingApp ? '更新失败' : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await appApi.delete(id);
      message.success('应用已删除');
      fetchApps();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
    {
      title: '开发语言',
      dataIndex: 'language',
      key: 'language',
      width: 100,
      render: (v: string) => v && <Tag>{v}</Tag>,
    },
    {
      title: '业务线',
      dataIndex: 'business_line_name',
      key: 'business_line',
      width: 120,
      render: (v: string) => <Tag color="geekblue">{v || '-'}</Tag>,
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner',
      width: 120,
      render: (v: string) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] || 'default'}>{STATUS_LABELS[v] || v}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
    },

  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>应用管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          新建应用
        </Button>
      </div>

      <Table
        dataSource={apps}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSize: 10,
        }}
        scroll={{ x: 900 }}
        onRow={(record) => ({
          onClick: () => navigate(`/apps/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />

      <Modal
        title={editingApp ? '编辑应用' : '新建应用'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={600}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入应用名称' }]}
          >
            <Input placeholder="例如：用户中心" />
          </Form.Item>
          <Form.Item
            name="code"
            label="编码"
            rules={[{ required: true, message: '请输入应用编码' }]}
          >
            <Input placeholder="例如：user-center" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="应用描述" />
          </Form.Item>
          <Form.Item
            name="language"
            label="开发语言"
            rules={[{ required: true, message: '请选择开发语言' }]}
          >
            <Select options={LANGUAGE_OPTIONS} />
          </Form.Item>
          <Form.Item name="repo_url" label="代码仓库地址">
            <Input placeholder="https://github.com/example/repo" />
          </Form.Item>
          <Form.Item
            name="business_line"
            label="业务线"
            rules={[{ required: true, message: '请选择业务线' }]}
          >
            <Select
              placeholder="请选择业务线"
              showSearch
              optionFilterProp="label"
              options={businessLines.map((bl: any) => ({
                value: bl.id,
                label: bl.name,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="owner"
            label="负责人"
            rules={[{ required: true, message: '请选择负责人' }]}
          >
            <Select
              placeholder="请选择负责人"
              showSearch
              optionFilterProp="label"
              options={users.map((u: any) => ({
                value: u.id,
                label: `${u.display_name} (${u.username})`,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}