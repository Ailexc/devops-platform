import { useEffect, useState } from 'react';
import { Tabs, Table, Button, Modal, Form, Input, InputNumber, Switch, Select, Tag, message, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { infraApi } from '../../api';

const { Title } = Typography;

interface Environment {
  id: number;
  name: string;
  code: string;
  sort_order: number;
  is_production: boolean;
  deploy_type: string;
}

interface Cluster {
  id: number;
  name: string;
  code: string;
  api_server: string;
  environment_id: number;
  environment_name: string;
  status: string;
}

interface Namespace {
  id: number;
  name: string;
  cluster_name: string;
  environment_name: string;
  created_at: string;
}

export default function InfraPage() {
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [namespaces, setNamespaces] = useState<Namespace[]>([]);
  const [envLoading, setEnvLoading] = useState(false);
  const [clusterLoading, setClusterLoading] = useState(false);
  const [nsLoading, setNsLoading] = useState(false);

  // Environment modal
  const [envModalOpen, setEnvModalOpen] = useState(false);
  const [envForm] = Form.useForm();
  const [envSubmitting, setEnvSubmitting] = useState(false);

  // Cluster modal
  const [clusterModalOpen, setClusterModalOpen] = useState(false);
  const [clusterForm] = Form.useForm();
  const [clusterSubmitting, setClusterSubmitting] = useState(false);

  const loadEnvironments = () => {
    setEnvLoading(true);
    infraApi.environments.list().then((res: any) => {
      // API now returns {code: 200, data: [...]}
      setEnvironments(res?.data || []);
    }).finally(() => setEnvLoading(false));
  };

  const loadClusters = () => {
    setClusterLoading(true);
    infraApi.clusters.list().then((res: any) => {
      setClusters(res.data || []);
    }).finally(() => setClusterLoading(false));
  };

  const loadNamespaces = () => {
    setNsLoading(true);
    infraApi.namespaces.list().then((res: any) => {
      setNamespaces(res.data || []);
    }).finally(() => setNsLoading(false));
  };

  useEffect(() => {
    loadEnvironments();
    loadClusters();
    loadNamespaces();
  }, []);

  const handleCreateEnvironment = async (values: any) => {
    setEnvSubmitting(true);
    try {
      await infraApi.environments.create(values);
      message.success('环境创建成功');
      setEnvModalOpen(false);
      envForm.resetFields();
      loadEnvironments();
    } catch {
      message.error('创建失败');
    } finally {
      setEnvSubmitting(false);
    }
  };

  const handleCreateCluster = async (values: any) => {
    setClusterSubmitting(true);
    try {
      await infraApi.clusters.create(values);
      message.success('集群创建成功');
      setClusterModalOpen(false);
      clusterForm.resetFields();
      loadClusters();
    } catch {
      message.error('创建失败');
    } finally {
      setClusterSubmitting(false);
    }
  };

  const envColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
    {
      title: '是否生产',
      dataIndex: 'is_production',
      key: 'is_production',
      width: 100,
      render: (v: boolean) => v ? <Tag color="red">生产</Tag> : <Tag color="blue">非生产</Tag>,
    },
    {
      title: '部署类型',
      dataIndex: 'deploy_type',
      key: 'deploy_type',
      width: 110,
      render: (v: string) => <Tag color={v === 'k8s' ? 'blue' : 'orange'}>{v === 'k8s' ? 'Kubernetes' : 'EC2 / 虚拟机'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: () => (
        <Button type="link" disabled>编辑</Button>
      ),
    },
  ];

  const clusterColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    { title: 'API Server', dataIndex: 'api_server', key: 'api_server', ellipsis: true },
    { title: '所属环境', dataIndex: 'environment_name', key: 'environment_name' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => {
        const color = v === 'active' ? 'green' : v === 'inactive' ? 'default' : 'orange';
        return <Tag color={color}>{v}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: () => (
        <Button type="link" disabled>编辑</Button>
      ),
    },
  ];

  const nsColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '所属集群', dataIndex: 'cluster_name', key: 'cluster_name' },
    { title: '所属环境', dataIndex: 'environment_name', key: 'environment_name' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ];

  const tabItems = [
    {
      key: 'environments',
      label: '环境管理',
      children: (
        <div>
          <div style={{ marginBottom: 16, textAlign: 'right' }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setEnvModalOpen(true)}>
              新建环境
            </Button>
          </div>
          <Table
            dataSource={environments}
            columns={envColumns}
            rowKey="id"
            loading={envLoading}
            pagination={false}
          />
        </div>
      ),
    },
    {
      key: 'clusters',
      label: '集群管理',
      children: (
        <div>
          <div style={{ marginBottom: 16, textAlign: 'right' }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setClusterModalOpen(true)}>
              新建集群
            </Button>
          </div>
          <Table
            dataSource={clusters}
            columns={clusterColumns}
            rowKey="id"
            loading={clusterLoading}
            pagination={false}
          />
        </div>
      ),
    },
    {
      key: 'namespaces',
      label: '命名空间',
      children: (
        <Table
          dataSource={namespaces}
          columns={nsColumns}
          rowKey="id"
          loading={nsLoading}
          pagination={false}
        />
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>环境与集群管理</Title>
      <Tabs items={tabItems} />

      {/* 新建环境 Modal */}
      <Modal
        title="新建环境"
        open={envModalOpen}
        onCancel={() => { setEnvModalOpen(false); envForm.resetFields(); }}
        footer={null}
        destroyOnHidden
      >
        <Form form={envForm} onFinish={handleCreateEnvironment} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入环境名称' }]}>
            <Input placeholder="例如: 生产环境" />
          </Form.Item>
          <Form.Item name="code" label="编码" rules={[{ required: true, message: '请输入环境编码' }]}>
            <Input placeholder="例如: production" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_production" label="是否生产环境" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={envSubmitting} block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 新建集群 Modal */}
      <Modal
        title="新建集群"
        open={clusterModalOpen}
        onCancel={() => { setClusterModalOpen(false); clusterForm.resetFields(); }}
        footer={null}
        destroyOnHidden
      >
        <Form form={clusterForm} onFinish={handleCreateCluster} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入集群名称' }]}>
            <Input placeholder="例如: 上海生产集群" />
          </Form.Item>
          <Form.Item name="code" label="编码" rules={[{ required: true, message: '请输入集群编码' }]}>
            <Input placeholder="例如: sh-production" />
          </Form.Item>
          <Form.Item name="api_server" label="API Server" rules={[{ required: true, message: '请输入 API Server 地址' }]}>
            <Input placeholder="https://k8s.example.com" />
          </Form.Item>
          <Form.Item
            name="environment_id"
            label="所属环境"
            rules={[{ required: true, message: '请选择所属环境' }]}
          >
            <Select
              placeholder="选择环境"
              options={environments.map((env) => ({
                value: env.id,
                label: env.name,
              }))}
            />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select
              options={[
                { value: 'active', label: '活跃' },
                { value: 'inactive', label: '停用' },
                { value: 'maintenance', label: '维护中' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={clusterSubmitting} block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}