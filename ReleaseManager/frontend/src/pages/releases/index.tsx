import { useEffect, useState } from 'react';
import { Table, Tag, Typography, Space, Button, Tooltip } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { appApi, releaseApi } from '../../api';

const { Title } = Typography;

const RELEASE_STATUS_COLORS: Record<string, string> = {
  pending: 'orange', approved: 'blue', running: 'cyan',
  completed: 'green', failed: 'red', rolled_back: 'purple', cancelled: 'default',
};
const RELEASE_STATUS_LABELS: Record<string, string> = {
  pending: '待审批', approved: '已审批', running: '发布中',
  completed: '已完成', failed: '失败', rolled_back: '已回滚', cancelled: '已取消',
};
const RELEASE_MODE_LABELS: Record<string, string> = {
  regular: '常规发布', incremental: '增量发布', compensation: '补偿发布',
  quick: '快速发布', rollback: '回滚发布', scale: '实例伸缩',
};
const RELEASE_MODE_COLORS: Record<string, string> = {
  regular: 'blue', incremental: 'cyan', compensation: 'orange',
  quick: 'purple', rollback: 'red', scale: 'geekblue',
};
const DEPLOY_MODE_MAP: Record<string, { color: string; label: string }> = {
  EC2: { color: 'blue', label: 'EC2' }, k8s: { color: 'green', label: 'K8s' },
};
const PERMISSION_SOURCE_MAP: Record<string, { color: string; label: string }> = {
  own_group: { color: 'blue', label: '组内应用' }, cross_group: { color: 'purple', label: '协作应用' },
};

export default function ReleaseListPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [releasesByApp, setReleasesByApp] = useState<Record<number, any[]>>({});
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [appsRes, releasesRes] = await Promise.all([
        appApi.list(),
        releaseApi.list({ page_size: 9999 }),
      ]);
      const appList = Array.isArray(appsRes) ? appsRes : (appsRes?.data || []);
      const allReleases = releasesRes?.data || [];
      const grouped: Record<number, any[]> = {};
      allReleases.forEach((r: any) => {
        const appId = typeof r.application === 'object' ? r.application?.id : r.application;
        if (appId) {
          if (!grouped[appId]) grouped[appId] = [];
          grouped[appId].push(r);
        }
      });
      setApps(appList);
      setReleasesByApp(grouped);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const columns = [
    {
      title: '应用名称', dataIndex: 'name', key: 'name', width: 160,
      render: (v: string) => <Typography.Text strong>{v}</Typography.Text>,
    },
    {
      title: '编码', dataIndex: 'code', key: 'code', width: 120,
      render: (v: string) => <Typography.Text code>{v}</Typography.Text>,
    },
    {
      title: '开发语言', dataIndex: 'language', key: 'language', width: 100,
      render: (v: string) => v ? <Tag>{v}</Tag> : '-',
    },
    {
      title: '部署模式', dataIndex: 'deploy_mode', key: 'deploy_mode', width: 100,
      render: (v: string) => {
        const mode = DEPLOY_MODE_MAP[v] || { color: 'default', label: v || '-' };
        return <Tag color={mode.color}>{mode.label}</Tag>;
      },
    },
    {
      title: '最近发布', key: 'recent_release', width: 360,
      render: (_: any, record: any) => {
        const releases = releasesByApp[record.id] || [];
        if (releases.length === 0) return <Typography.Text type="secondary">暂无发布</Typography.Text>;
        const latest = releases[0];
        const ci = (latest.tasks || []).find((t: any) => t.stage === 'ci');
        const cd = (latest.tasks || []).find((t: any) => t.stage === 'cd');
        const envName = typeof latest.environment === 'object' ? latest.environment?.name : '';
        return (
          <Space size={6} wrap>
            <Tag color={RELEASE_MODE_COLORS[latest.release_mode] || 'blue'} style={{ fontSize: 11 }}>
              {RELEASE_MODE_LABELS[latest.release_mode] || '常规发布'}
            </Tag>
            {envName && <Tag color="blue" style={{ fontSize: 11 }}>{envName}</Tag>}
            <Typography.Text style={{ fontSize: 13 }}>{latest.version || '-'}</Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              CI {ci?.status === 'success' ? '✅' : ci?.status === 'running' ? '🔄' : ci?.status === 'failed' ? '❌' : '—'}
            </Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              CD {cd?.status === 'success' ? '✅' : cd?.status === 'running' ? '🔄' : cd?.status === 'failed' ? '❌' : '—'}
            </Typography.Text>
            <Tag color={RELEASE_STATUS_COLORS[latest.status] || 'default'} style={{ fontSize: 11 }}>
              {latest.status === 'failed'
                ? (latest.ci_status === 'failed' ? 'CI失败' : latest.cd_status === 'failed' ? 'CD失败' : '失败')
                : (RELEASE_STATUS_LABELS[latest.status] || latest.status)
              }
            </Tag>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>共{releases.length}条</Typography.Text>
          </Space>
        );
      },
    },
    {
      title: '归属类型', dataIndex: 'permission_source', key: 'permission_source', width: 100,
      render: (v: string) => {
        const cfg = PERMISSION_SOURCE_MAP[v] || { color: 'default', label: v || '-' };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: '负责人', key: 'owner', width: 100,
      render: (_: any, record: any) => {
        const owners = [record.owner_name, record.product_owner_name, record.ops_owner_name].filter(Boolean);
        if (owners.length === 0) return <Typography.Text type="secondary">-</Typography.Text>;
        return (
          <Tooltip title={owners.length > 1 ? owners.join(' / ') : undefined}>
            <Typography.Text>{owners[0]}</Typography.Text>
          </Tooltip>
        );
      },
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>应用列表</Title>
        <Button icon={<ReloadOutlined />} onClick={fetchData} loading={loading}>刷新</Button>
      </div>
      <Table
        dataSource={apps}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
        scroll={{ x: 1100 }}
        locale={{ emptyText: '暂无有权限的应用' }}
        onRow={(record) => ({
          onClick: () => navigate(`/releases/app/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
}