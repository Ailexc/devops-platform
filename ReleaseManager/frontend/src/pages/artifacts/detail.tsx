import { useEffect, useState } from 'react';
import {
  Typography, Descriptions, Tag, Card, Steps, Button, Space, Row, Col, Statistic, Spin, Empty, Tooltip,
} from 'antd';
import {
  ArrowLeftOutlined, ClockCircleOutlined, CodeOutlined, CloudServerOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { artifactApi } from '../../api';

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

const PROMOTION_STATUS: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  pending: { color: 'orange', icon: <SyncOutlined spin />, label: '待晋级' },
  promoted: { color: 'green', icon: <CheckCircleOutlined />, label: '已晋级' },
  rejected: { color: 'red', icon: <CloseCircleOutlined />, label: '已驳回' },
  rolled_back: { color: 'default', icon: <CloseCircleOutlined />, label: '已回退' },
};

function formatDuration(seconds: number): string {
  if (!seconds) return '-';
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ArtifactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [artifact, setArtifact] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    artifactApi.detail(Number(id)).then((res: any) => {
      setArtifact(res.data || res);
    }).catch(() => {
      // API 错误（如 401）会被拦截器处理跳转登录
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!artifact) return <Empty description="制品不存在或无权访问" />;

  const promotions = artifact.promotions || [];
  const currentEnvColor = artifact.current_env?.startsWith('dev') ? 'dev'
    : artifact.current_env?.startsWith('test') ? 'test'
    : artifact.current_env?.startsWith('pre') ? 'staging'
    : artifact.current_env?.startsWith('prod') ? 'prod' : 'default';

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/artifacts')}>返回</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {artifact.application_name} / {artifact.version}
        </Typography.Title>
        <Tag color={ENV_COLORS[currentEnvColor] || 'default'} style={{ fontSize: 14 }}>
          {ENV_LABELS[artifact.current_env] || artifact.current_env || '未知'}
        </Tag>
      </Space>

      {/* 基本信息卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small"><Statistic title="制品类型" value={ARTIFACT_TYPE_LABELS[artifact.artifact_type] || artifact.artifact_type} prefix={<CloudServerOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="构建耗时" value={formatDuration(artifact.build_duration)} prefix={<ClockCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="构建分支" value={artifact.branch || '-'} prefix={<CodeOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card size="small"><Statistic title="晋级次数" value={promotions.length} prefix={<SyncOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={16}>
        {/* 左侧：制品详情 */}
        <Col span={14}>
          <Card title="制品信息" size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="应用">{artifact.application_name}</Descriptions.Item>
              <Descriptions.Item label="版本"><Text code strong>{artifact.version}</Text></Descriptions.Item>
              <Descriptions.Item label="制品类型"><Tag>{ARTIFACT_TYPE_LABELS[artifact.artifact_type] || artifact.artifact_type}</Tag></Descriptions.Item>
              <Descriptions.Item label="当前环境"><Tag color={ENV_COLORS[currentEnvColor]}>{ENV_LABELS[artifact.current_env] || artifact.current_env}</Tag></Descriptions.Item>
              <Descriptions.Item label="镜像 Tag" span={2}>
                {artifact.image_tag ? <Text code>{artifact.image_tag}</Text> : <Text type="secondary">-</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="存储路径" span={2}>
                {artifact.storage_path ? <Text code style={{ fontSize: 12 }}>{artifact.storage_path}</Text> : <Text type="secondary">-</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="构建分支">{artifact.branch || '-'}</Descriptions.Item>
              <Descriptions.Item label="Commit ID">
                {artifact.commit_id ? <Tooltip title={artifact.commit_id}><Text code>{artifact.commit_id.substring(0, 12)}</Text></Tooltip> : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="构建耗时">{formatDuration(artifact.build_duration)}</Descriptions.Item>
              <Descriptions.Item label="文件大小">{formatFileSize(artifact.file_size)}</Descriptions.Item>
              <Descriptions.Item label="制品仓库" span={2}>{artifact.repository_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="构建链接" span={2}>
                {artifact.build_job_url ? <a href={artifact.build_job_url} target="_blank" rel="noreferrer">{artifact.build_job_url}</a> : <Text type="secondary">-</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="创建人">{artifact.created_by_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{artifact.created_at}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* 右侧：晋级历史 */}
        <Col span={10}>
          <Card title={`晋级历史 (${promotions.length})`} size="small">
            {promotions.length === 0 ? (
              <Empty description="暂无晋级记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <div style={{ maxHeight: 500, overflow: 'auto' }}>
                {promotions.map((p: any, idx: number) => {
                  const statusInfo = PROMOTION_STATUS[p.status] || PROMOTION_STATUS.pending;
                  return (
                    <Card key={p.id} size="small" style={{ marginBottom: 8 }}
                      title={
                        <Space>
                          <Tag color={statusInfo.color} icon={statusInfo.icon}>{statusInfo.label}</Tag>
                          <Text strong>{ENV_LABELS[p.from_env_name] || p.from_env_name}</Text>
                          <Text type="secondary">→</Text>
                          <Text strong>{ENV_LABELS[p.to_env_name] || p.to_env_name}</Text>
                        </Space>
                      }
                      extra={<Text type="secondary" style={{ fontSize: 12 }}>{p.promoted_at}</Text>}
                    >
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">操作人: {p.promoted_by_name || '-'}</Text>
                        {p.comment && <Text type="secondary">备注: {p.comment}</Text>}
                      </Space>
                    </Card>
                  );
                })}
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
