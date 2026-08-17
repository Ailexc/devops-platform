import { useEffect, useState, useCallback } from 'react';
import {
  Table, Tag, Typography, Space, Button, Select, Input, Tooltip, Card, Row, Col, Statistic,
} from 'antd';
import {
  SearchOutlined, ApartmentOutlined, CloudServerOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { artifactApi, appApi } from '../../api';

const { Text } = Typography;

const ENV_COLORS: Record<string, string> = {
  dev: 'blue', test: 'green', staging: 'orange', prod: 'red',
};
const ENV_LABELS: Record<string, string> = {
  dev: '开发', dev2: '开发2', test1: '测试1', test2: '测试2', test3: '测试3',
  pre1: '预发1', pre2: '预发2', prod1: '生产1', prod2: '生产2',
};

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  docker_image: 'Docker 镜像', jar: 'JAR', war: 'WAR',
  npm_package: 'NPM', python_wheel: 'Wheel', binary: '二进制',
  helm_chart: 'Helm Chart',
};

function formatDuration(seconds: number): string {
  if (!seconds) return '-';
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

export default function ArtifactListPage() {
  const navigate = useNavigate();
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [appOptions, setAppOptions] = useState<any[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<number | undefined>();
  const [envFilter, setEnvFilter] = useState<string | undefined>();
  const [versionSearch, setVersionSearch] = useState('');

  const fetchArtifacts = useCallback(() => {
    setLoading(true);
    const params: any = {};
    if (selectedAppId) params.app_id = selectedAppId;
    if (envFilter) params.env_type = envFilter;
    if (versionSearch) params.version = versionSearch;
    artifactApi.list(params).then((res: any) => {
      setArtifacts(res.data || []);
    }).finally(() => setLoading(false));
  }, [selectedAppId, envFilter, versionSearch]);

  const fetchApps = () => {
    appApi.list().then((res: any) => {
      setAppOptions(res.data || []);
    });
  };

  useEffect(() => { fetchApps(); }, []);
  useEffect(() => { fetchArtifacts(); }, [fetchArtifacts]);

  const stats = {
    total: artifacts.length,
    dev: artifacts.filter((a: any) => a.current_env?.startsWith('dev')).length,
    test: artifacts.filter((a: any) => a.current_env?.startsWith('test')).length,
    staging: artifacts.filter((a: any) => a.current_env?.startsWith('pre')).length,
    prod: artifacts.filter((a: any) => a.current_env?.startsWith('prod')).length,
  };

  const columns = [
    {
      title: '应用', key: 'app', width: 160,
      render: (_: any, r: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{r.application_name}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{r.application_code}</Text>
        </Space>
      ),
    },
    {
      title: '版本', dataIndex: 'version', key: 'version', width: 120,
      render: (v: string) => <Text code strong>{v}</Text>,
    },
    {
      title: '类型', dataIndex: 'artifact_type', key: 'artifact_type', width: 110,
      render: (v: string) => <Tag>{ARTIFACT_TYPE_LABELS[v] || v}</Tag>,
    },
    {
      title: '当前环境', dataIndex: 'current_env', key: 'current_env', width: 100,
      render: (v: string) => {
        if (!v) return <Text type="secondary">-</Text>;
        const colorKey = v.startsWith('dev') ? 'dev' : v.startsWith('test') ? 'test'
          : v.startsWith('pre') ? 'staging' : v.startsWith('prod') ? 'prod' : 'default';
        return <Tag color={ENV_COLORS[colorKey] || 'default'}>{ENV_LABELS[v] || v}</Tag>;
      },
    },
    {
      title: '镜像 Tag', dataIndex: 'image_tag', key: 'image_tag', width: 180,
      render: (v: string) => v ? <Text code style={{ fontSize: 12 }}>{v}</Text> : <Text type="secondary">-</Text>,
    },
    {
      title: '分支', dataIndex: 'branch', key: 'branch', width: 100,
      render: (v: string) => v ? <Tag>{v}</Tag> : '-',
    },
    {
      title: 'Commit', dataIndex: 'commit_id', key: 'commit_id', width: 100,
      render: (v: string) => v ? <Tooltip title={v}><Text code style={{ fontSize: 12 }}>{v.substring(0, 8)}</Text></Tooltip> : '-',
    },
    {
      title: '构建耗时', dataIndex: 'build_duration', key: 'build_duration', width: 90,
      render: (v: number) => formatDuration(v),
    },
    {
      title: '晋级', dataIndex: 'promotion_count', key: 'promotion_count', width: 70,
      render: (v: number) => v > 0 ? <Tag color="purple">{v} 次</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160,
    },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: any, r: any) => (
        <Button type="link" size="small" onClick={() => navigate(`/artifacts/${r.id}`)}>
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}>制品管理</Typography.Title>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small"><Statistic title="制品总数" value={stats.total} prefix={<ApartmentOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="开发环境" value={stats.dev} valueStyle={{ color: '#1677ff' }} prefix={<CloudServerOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="测试环境" value={stats.test} valueStyle={{ color: '#52c41a' }} prefix={<CloudServerOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="生产环境" value={stats.prod} valueStyle={{ color: '#ff4d4f' }} prefix={<CloudServerOutlined />} /></Card>
        </Col>
      </Row>

      <Card size="small"
        extra={
          <Space>
            <Select placeholder="按应用筛选" allowClear style={{ width: 180 }} value={selectedAppId}
              onChange={(v) => setSelectedAppId(v)}
              options={appOptions.map((a: any) => ({ value: a.id, label: a.name }))}
            />
            <Select placeholder="按环境筛选" allowClear style={{ width: 120 }} value={envFilter}
              onChange={(v) => setEnvFilter(v)}
              options={[
                { value: 'dev', label: '开发' }, { value: 'test', label: '测试' },
                { value: 'staging', label: '预发' }, { value: 'prod', label: '生产' },
              ]}
            />
            <Input placeholder="版本号搜索" prefix={<SearchOutlined />} style={{ width: 160 }}
              value={versionSearch} onChange={(e) => setVersionSearch(e.target.value)}
              onPressEnter={fetchArtifacts} allowClear
            />
          </Space>
        }
      >
        <Table dataSource={artifacts} columns={columns} rowKey="id" loading={loading}
          pagination={{ showSizeChanger: true, showQuickJumper: true, showTotal: (t) => `共 ${t} 条`, pageSize: 15, defaultPageSize: 15 }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>
    </div>
  );
}
