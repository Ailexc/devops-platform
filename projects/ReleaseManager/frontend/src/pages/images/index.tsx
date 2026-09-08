import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Select, Input, Tag, Typography, Space, message, Popconfirm,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { imageApi } from '../../api';

const { Title } = Typography;

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'go', label: 'Go' },
  { value: 'node', label: 'Node.js' },
  { value: 'java', label: 'Java' },
  { value: 'other', label: '其他' },
];

export default function ImageRegistryPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchData = () => {
    setLoading(true);
    imageApi.list().then((res: any) => {
      setData(res?.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCreateModal = () => {
    setEditingItem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const openEditModal = (record: any) => {
    setEditingItem(record);
    form.setFieldsValue({
      language: record.language,
      registry: record.registry || 'docker.io',
      builder_image: record.builder_image,
      base_image: record.base_image,
      description: record.description,
    });
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editingItem) {
        await imageApi.update(editingItem.id, values);
        message.success('更新成功');
      } else {
        await imageApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchData();
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error(editingItem ? '更新失败' : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await imageApi.delete(id);
      message.success('已删除');
      fetchData();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '开发语言',
      dataIndex: 'language_display',
      key: 'language',
      width: 100,
      render: (_: any, record: any) => {
        const colors: Record<string, string> = { python: 'green', go: 'blue', node: 'cyan', java: 'orange', other: 'default' };
        return <Tag color={colors[record.language] || 'default'}>{record.language_display}</Tag>;
      },
    },
    {
      title: '镜像仓库来源',
      dataIndex: 'registry',
      key: 'registry',
      width: 220,
      render: (v: string) => <code style={{ fontSize: 12 }}>{v || 'docker.io'}</code>,
    },
    {
      title: '环境基础镜像（CI）',
      dataIndex: 'builder_image',
      key: 'builder_image',
      width: 240,
      render: (v: string) => <code style={{ fontSize: 13 }}>{v}</code>,
    },
    {
      title: '应用基础镜像（CD）',
      dataIndex: 'base_image',
      key: 'base_image',
      width: 240,
      render: (v: string) => <code style={{ fontSize: 13 }}>{v}</code>,
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)} okText="确定" cancelText="取消">
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>镜像注册表</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          新增镜像配置
        </Button>
      </div>

      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
        locale={{ emptyText: '暂无镜像配置' }}
      />

      <Modal
        title={editingItem ? '编辑镜像配置' : '新增镜像配置'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleSubmit}
        confirmLoading={submitting}
        width={560}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="language"
            label="开发语言"
            rules={[{ required: true, message: '请选择开发语言' }]}
          >
            <Select
              placeholder="请选择开发语言"
              disabled={!!editingItem}
              options={LANGUAGE_OPTIONS}
            />
          </Form.Item>
          <Form.Item
            name="registry"
            label="镜像仓库来源"
            tooltip="Docker 镜像仓库地址前缀。Docker Hub 用 docker.io，阿里云用 registry.cn-hangzhou.aliyuncs.com"
            initialValue="docker.io"
          >
            <Select
              showSearch
              options={[
                { value: 'docker.io', label: 'docker.io（Docker Hub 官方）' },
                { value: 'registry.cn-hangzhou.aliyuncs.com', label: 'registry.cn-hangzhou.aliyuncs.com（阿里云）' },
                { value: 'registry.cn-beijing.aliyuncs.com', label: 'registry.cn-beijing.aliyuncs.com（阿里云北京）' },
                { value: 'ghcr.io', label: 'ghcr.io（GitHub Container Registry）' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="builder_image"
            label="环境基础镜像（CI 构建用）"
            rules={[{ required: true, message: '请输入环境基础镜像' }]}
            tooltip="包含编译器/工具链的镜像，用于 CI 阶段的代码编译构建，用完即销毁。例如 golang:1.23-alpine"
          >
            <Input placeholder="例如：golang:1.23-alpine" />
          </Form.Item>
          <Form.Item
            name="base_image"
            label="应用基础镜像（CD 运行用）"
            rules={[{ required: true, message: '请输入应用基础镜像' }]}
            tooltip="预装应用运行所需环境的镜像，不含编译工具，作为最终运行镜像的基础层。例如 alpine:3.20"
          >
            <Input placeholder="例如：alpine:3.20" />
          </Form.Item>
          <Form.Item name="description" label="说明">
            <Input.TextArea rows={2} placeholder="可选，描述该镜像配置的用途" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
