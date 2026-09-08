import { useEffect, useState } from 'react';
import {
  Card, Table, Tag, Typography, Space, Button, Steps, Badge, Modal, Descriptions, Result,
} from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { authzApi } from '../../api';

const { Title, Text } = Typography;

const REQUEST_TYPE_MAP: Record<string, string> = {
  apply: '申请权限',
  share: '分享协作应用',
  revoke: '回收协作权限',
  release: '解除协作应用',
};

const STATUS_MAP: Record<string, { text: string; color: string }> = {
  pending: { text: '待审批', color: 'orange' },
  approved: { text: '已通过', color: 'green' },
  rejected: { text: '已拒绝', color: 'red' },
};

export default function RelatedToMePage() {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authzApi.permissionRequests.relatedList();
      setRecords(res?.data || []);
    } catch {
      setError('加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (v: string) => {
    if (!v) return '-';
    return v.replace('T', ' ').slice(0, 19);
  };

  const columns = [
    {
      title: '申请类型',
      dataIndex: 'request_type',
      width: 140,
      render: (v: string) => REQUEST_TYPE_MAP[v] || v,
    },
    {
      title: '申请人',
      dataIndex: 'user_name',
      width: 120,
    },
    {
      title: '应用 / 环境',
      width: 220,
      render: (_: any, record: any) => (
        <Space orientation="vertical" size={0}>
          <Text strong>{record.app_name || `应用 #${record.app_id}`}</Text>
          <Tag color="default" style={{ fontSize: '10px' }}>{record.env_type_label || record.env_type}</Tag>
        </Space>
      ),
    },
    {
      title: '授权范围',
      dataIndex: 'grant_scope',
      width: 120,
      render: (v: string) => (v === 'cross_group' ? <Tag color="orange">跨组协作</Tag> : <Tag color="blue">本组权限</Tag>),
    },
    {
      title: '审批进展',
      key: 'progress',
      width: 220,
      render: (_: any, record: any) => {
        const progress = record.approval_progress;
        if (!progress) return <Text type="secondary">无需审批</Text>;
        return (
          <Space orientation="vertical" size={0} style={{ width: '100%' }}>
            <Text style={{ fontSize: 12 }}>
              已通过 {progress.approved}/{progress.total}
              {progress.rejected > 0 && <span style={{ color: '#cf1322', marginLeft: 8 }}>已拒绝 {progress.rejected}</span>}
            </Text>
            <Steps
              size="small"
              current={progress.approved}
              status={progress.rejected > 0 ? 'error' : 'process'}
              items={progress.steps.map((s: any) => ({
                title: '',
                status: s.action === 'approved' ? 'finish' : s.action === 'rejected' ? 'error' : 'wait',
              }))}
            />
          </Space>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: string) => {
        const conf = STATUS_MAP[v] || { text: v, color: 'default' };
        return <Badge status={conf.color as any} text={conf.text} />;
      },
    },
    {
      title: '申请时间',
      dataIndex: 'created_at',
      width: 160,
      render: (v: string) => formatTime(v),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setDetail(record)}>
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>与我相关</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        展示以您或您所在组为受益人的权限申请记录。
      </Text>

      <Card size="small">
        {error ? (
          <Result
            status="error"
            title="加载失败"
            subTitle={error}
            extra={<Button type="primary" onClick={loadRecords}>重新加载</Button>}
          />
        ) : (
          <Table
            dataSource={records}
            columns={columns}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: '暂无与您相关的权限申请记录' }}
          />
        )}
      </Card>

      <Modal
        title="申请详情"
        open={!!detail}
        onCancel={() => setDetail(null)}
        footer={null}
        width={640}
      >
        {detail && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="申请类型" span={1}>{REQUEST_TYPE_MAP[detail.request_type] || detail.request_type}</Descriptions.Item>
            <Descriptions.Item label="申请人" span={1}>{detail.user_name || `用户 #${detail.user}`}</Descriptions.Item>
            <Descriptions.Item label="当前状态" span={1}>
              <Tag color={STATUS_MAP[detail.status]?.color || 'default'}>{STATUS_MAP[detail.status]?.text || detail.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="授权范围" span={1}>{detail.grant_scope === 'cross_group' ? '跨组协作' : '本组权限'}</Descriptions.Item>
            <Descriptions.Item label="应用" span={1}>{detail.app_name || `应用 #${detail.app_id}`}</Descriptions.Item>
            <Descriptions.Item label="环境类型" span={1}>{detail.env_type_label || detail.env_type}</Descriptions.Item>
            <Descriptions.Item label="申请原因" span={2}>{detail.reason || '-'}</Descriptions.Item>
            <Descriptions.Item label="申请时间" span={1}>{formatTime(detail.created_at)}</Descriptions.Item>
            <Descriptions.Item label="更新时间" span={1}>{formatTime(detail.updated_at)}</Descriptions.Item>
          </Descriptions>
        )}
        {detail?.approval_progress && (
          <div style={{ marginTop: 16 }}>
            <Text strong>审批进展</Text>
            <Steps
              orientation="vertical"
              size="small"
              current={detail.approval_progress.approved}
              status={detail.approval_progress.rejected > 0 ? 'error' : 'process'}
              items={detail.approval_progress.steps.map((s: any) => ({
                title: s.step_name,
                description: (
                  <Space orientation="vertical" size={0}>
                    <Text style={{ fontSize: 12 }}>审批人: {s.approver_name || '-'}</Text>
                    <Text style={{ fontSize: 12 }}>状态: {s.action === 'approved' ? '已通过' : s.action === 'rejected' ? '已拒绝' : '待审批'}</Text>
                    {s.comment && <Text style={{ fontSize: 12 }}>意见: {s.comment}</Text>}
                  </Space>
                ),
              }))}
              style={{ marginTop: 12 }}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}