import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Typography } from 'antd';
import {
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { dashboardApi } from '../../api';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

export default function DashboardPage() {
  const [stats, setStats] = useState<any>({});
  const [recentReleases, setRecentReleases] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    dashboardApi.stats().then((res: any) => setStats(res.data || {}));
    dashboardApi.recentReleases().then((res: any) => setRecentReleases(res.data || []));
    dashboardApi.myPendingApprovals().then((res: any) => setPendingApprovals(res.data || []));
  }, []);

  const statusColors: Record<string, string> = {
    pending: 'orange',
    running: 'blue',
    completed: 'green',
    failed: 'red',
    rolled_back: 'purple',
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="总发布次数" value={stats.total_releases || 0} prefix={<SendOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="今日发布" value={stats.today_releases || 0} prefix={<ClockCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="发布成功率" value={stats.success_rate || 0} suffix="%" prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="待审批" value={stats.pending_approvals || 0} prefix={<CloseCircleOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={14}>
          <Card title="近期发布">
            <Table
              dataSource={recentReleases}
              rowKey="id"
              size="small"
              pagination={false}
              onRow={(record: any) => ({
                onClick: () => navigate(`/releases/${record.id}`),
                style: { cursor: 'pointer' },
              })}
              columns={[
                { title: '发布单号', dataIndex: 'release_no', width: 180 },
                { title: '标题', dataIndex: 'title', ellipsis: true },
                {
                  title: '状态',
                  dataIndex: 'status',
                  width: 100,
                  render: (status: string) => (
                    <Tag color={statusColors[status]}>{status}</Tag>
                  ),
                },
                { title: '创建人', dataIndex: 'creator_name', width: 100 },
                { title: '时间', dataIndex: 'created_at', width: 160 },
              ]}
            />
          </Card>
        </Col>
        <Col span={10}>
          <Card title="我的待审批">
            <div>
              {pendingApprovals.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0', color: '#999' }}>暂无待审批</div>
              ) : (
                pendingApprovals.map((item: any, index: number) => (
                  <div
                    key={index}
                    onClick={() => navigate('/approvals')}
                    style={{ cursor: 'pointer', padding: '12px 0', borderBottom: index < pendingApprovals.length - 1 ? '1px solid #f0f0f0' : 'none' }}
                  >
                    <div style={{ fontWeight: 500 }}>{item.release_title || '权限申请'}</div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.created_at} · {item.approver_name}
                    </Text>
                  </div>
                ))
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}