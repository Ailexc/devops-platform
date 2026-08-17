import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Select, Tag, Popconfirm, message, Typography, Space,
} from 'antd';
import { EyeOutlined, RollbackOutlined } from '@ant-design/icons';
import { deployApi, appApi } from '../../api';

const { Title } = Typography;

interface DeployRecord {
  id: number;
  release_no: string;
  application_name: string;
  environment: string;
  version: string;
  image_tag: string;
  operation_type: string;
  strategy: string;
  status: string;
  executor: string;
  created_at: string;
}

interface PodInstance {
  id: number;
  name: string;
  node: string;
  ip: string;
  status: string;
  image: string;
  started_at: string;
}

interface AppOption {
  id: number;
  name: string;
}

const OPERATION_TYPE_COLORS: Record<string, string> = {
  deploy: 'blue',
  rollback: 'orange',
};

const STRATEGY_COLORS: Record<string, string> = {
  rolling: 'geekblue',
  recreate: 'purple',
  blue_green: 'cyan',
  canary: 'gold',
};

const STATUS_COLORS: Record<string, string> = {
  success: 'green',
  failed: 'red',
  in_progress: 'processing',
  pending: 'default',
  cancelled: 'default',
};

const STATUS_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  in_progress: '进行中',
  pending: '待执行',
  cancelled: '已取消',
};

const OPERATION_TYPE_LABELS: Record<string, string> = {
  deploy: '部署',
  rollback: '回滚',
};

const STRATEGY_LABELS: Record<string, string> = {
  rolling: '滚动更新',
  recreate: '重建',
  blue_green: '蓝绿部署',
  canary: '金丝雀',
};

export default function DeployHistoryPage() {
  const [deploys, setDeploys] = useState<DeployRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [appOptions, setAppOptions] = useState<AppOption[]>([]);
  const [selectedApp, setSelectedApp] = useState<string | undefined>(undefined);

  // Pod modal
  const [podModalVisible, setPodModalVisible] = useState(false);
  const [pods, setPods] = useState<PodInstance[]>([]);
  const [podLoading, setPodLoading] = useState(false);
  const [selectedDeploy, setSelectedDeploy] = useState<DeployRecord | null>(null);

  const fetchDeploys = () => {
    setLoading(true);
    deployApi.list().then((res: any) => {
      let data = res.data || [];
      if (selectedApp) {
        data = data.filter((item: DeployRecord) => item.application_name === selectedApp);
      }
      setDeploys(data);
    }).finally(() => setLoading(false));
  };

  const fetchApps = () => {
    appApi.list().then((res: any) => {
      setAppOptions(res.data || []);
    });
  };

  useEffect(() => {
    fetchDeploys();
    fetchApps();
  }, []);

  useEffect(() => {
    fetchDeploys();
  }, [selectedApp]);

  const handleViewPods = async (record: DeployRecord) => {
    setSelectedDeploy(record);
    setPodModalVisible(true);
    setPodLoading(true);
    try {
      const res: any = await deployApi.pods(record.id);
      setPods(res.data || []);
    } catch {
      message.error('获取 Pod 信息失败');
      setPods([]);
    } finally {
      setPodLoading(false);
    }
  };

  const handleRollback = async (id: number) => {
    try {
      await deployApi.rollback(id);
      message.success('回滚操作已发起');
      fetchDeploys();
    } catch {
      message.error('回滚失败');
    }
  };

  const podColumns = [
    { title: 'Pod名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '节点', dataIndex: 'node', key: 'node', width: 140 },
    { title: 'IP', dataIndex: 'ip', key: 'ip', width: 140 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => {
        const color = v === 'Running' ? 'green' : v === 'Pending' ? 'orange' : 'red';
        return <Tag color={color}>{v}</Tag>;
      },
    },
    { title: '镜像', dataIndex: 'image', key: 'image', ellipsis: true },
    { title: '启动时间', dataIndex: 'started_at', key: 'started_at', width: 170 },
  ];

  const columns = [
    { title: '发布单号', dataIndex: 'release_no', key: 'release_no', width: 150 },
    { title: '应用', dataIndex: 'application_name', key: 'application_name', width: 130 },
    { title: '环境', dataIndex: 'environment', key: 'environment', width: 100 },
    { title: '版本', dataIndex: 'version', key: 'version', width: 100 },
    { title: '镜像Tag', dataIndex: 'image_tag', key: 'image_tag', width: 120 },
    {
      title: '操作类型',
      dataIndex: 'operation_type',
      key: 'operation_type',
      width: 100,
      render: (v: string) => (
        <Tag color={OPERATION_TYPE_COLORS[v] || 'default'}>
          {OPERATION_TYPE_LABELS[v] || v}
        </Tag>
      ),
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
      width: 100,
      render: (v: string) => (
        <Tag color={STRATEGY_COLORS[v] || 'default'}>
          {STRATEGY_LABELS[v] || v}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] || 'default'}>
          {STATUS_LABELS[v] || v}
        </Tag>
      ),
    },
    { title: '执行人', dataIndex: 'executor', key: 'executor', width: 100 },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: DeployRecord) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewPods(record)}
          >
            查看Pod
          </Button>
          <Popconfirm
            title="确定要回滚该部署吗？"
            onConfirm={() => handleRollback(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              icon={<RollbackOutlined />}
            >
              回滚
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>部署历史</Title>
        <Select
          placeholder="按应用筛选"
          allowClear
          style={{ width: 200 }}
          value={selectedApp}
          onChange={(value) => setSelectedApp(value)}
          options={appOptions.map((app) => ({
            value: app.name,
            label: app.name,
          }))}
        />
      </div>

      <Table
        dataSource={deploys}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSize: 10,
        }}
        scroll={{ x: 1300 }}
      />

      <Modal
        title={`Pod 列表 - ${selectedDeploy?.release_no || ''}`}
        open={podModalVisible}
        onCancel={() => setPodModalVisible(false)}
        footer={null}
        width={900}
        destroyOnHidden
      >
        <Table
          dataSource={pods}
          columns={podColumns}
          rowKey="id"
          loading={podLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无 Pod 信息' }}
        />
      </Modal>
    </div>
  );
}