import { useEffect, useState, useCallback } from 'react';
import {
  Table, Tag, Typography, Space, Button, Modal, Input, message, Tabs, Descriptions,
} from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { approvalApi } from '../../api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const STATUS_COLORS: Record<string, string> = {
  pending: 'processing', approved: 'success', rejected: 'error',
};
const STATUS_LABELS: Record<string, string> = {
  pending: '待审批', approved: '已通过', rejected: '已驳回',
};
const ENV_COLORS: Record<string, string> = {
  dev: 'blue', test: 'green', staging: 'orange', prod: 'red',
};

export default function ReleaseApprovalPage() {
  const navigate = useNavigate();
  const [pendingList, setPendingList] = useState<any[]>([]);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [actionModalVisible, setActionModalVisible] = useState(false);
  const [actionType, setActionType] = useState<'approved' | 'rejected'>('approved');
  const [selectedApproval, setSelectedApproval] = useState<any>(null);
  const [actionComment, setActionComment] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);

  const fetchPending = useCallback(() => {
    setPendingLoading(true);
    approvalApi.pending({ type: 'release' }).then((res: any) => {
      setPendingList(res.data || []);
    }).finally(() => setPendingLoading(false));
  }, []);

  const fetchHistory = useCallback(() => {
    setHistoryLoading(true);
    approvalApi.list({ type: 'release' }).then((res: any) => {
      setHistoryList(res.data || []);
    }).finally(() => setHistoryLoading(false));
  }, []);

  useEffect(() => { fetchPending(); fetchHistory(); }, [fetchPending, fetchHistory]);

  const handleApprove = (record: any, type: 'approved' | 'rejected') => {
    setSelectedApproval(record);
    setActionType(type);
    setActionComment('');
    setActionModalVisible(true);
  };

  const confirmAction = async () => {
    if (!selectedApproval) return;
    setActionSubmitting(true);
    try {
      const apiFn = actionType === 'approved'
        ? () => approvalApi.approve(selectedApproval.id, actionComment)
        : () => approvalApi.reject(selectedApproval.id, actionComment);
      await apiFn();
      message.success(actionType === 'approved' ? '审批已通过' : '已驳回');
      setActionModalVisible(false);
      fetchPending();
      fetchHistory();
    } catch (e: any) {
      message.error(e?.message || '操作失败');
    } finally {
      setActionSubmitting(false);
    }
  };

  const getRel = (r: any) => r.release_detail || r.release || {};
  const APPROVAL_TYPE_LABELS: Record<string, string> = { release: '发布审批', scale: '实例伸缩' };
  const APPROVAL_TYPE_COLORS: Record<string, string> = { release: 'blue', scale: 'orange' };
  const pendingColumns = [
    {
      title: '类型', key: 'approval_type', width: 100,
      render: (_: any, r: any) => (
        <Tag color={APPROVAL_TYPE_COLORS[r.approval_type] || 'default'}>
          {APPROVAL_TYPE_LABELS[r.approval_type] || r.approval_type || '-'}
        </Tag>
      ),
    },
    {
      title: '发布单号', key: 'release_no', width: 180,
      render: (_: any, r: any) => {
        const rel = getRel(r);
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Text code>{`伸缩: ${d.app_name || '?'} → ${d.env_name || '?'}`}</Text>;
        }
        return <Text code>{rel.release_no || r.release_no || '-'}</Text>;
      },
    },
    {
      title: '应用', key: 'app', width: 140,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          return <Text strong>{(r.extra_data || {}).app_name || '-'}</Text>;
        }
        const rel = getRel(r);
        return <Text strong>{rel.application_name || '-'}</Text>;
      },
    },
    {
      title: '环境', key: 'env', width: 100,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Tag color={ENV_COLORS[d.env_code] || 'default'}>{d.env_name || '-'}</Tag>;
        }
        const rel = getRel(r);
        const code = rel.environment_code || '';
        return <Tag color={ENV_COLORS[code] || 'default'}>{rel.environment_name || '-'}</Tag>;
      },
    },
    {
      title: '详情', key: 'detail', width: 160,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Text type="secondary">{d.current_replicas} → {d.target_replicas} ({d.action_label || '-'})</Text>;
        }
        const rel = getRel(r);
        return <Text type="secondary">版本: {rel.version || '-'}</Text>;
      },
    },
    {
      title: '发起人', key: 'creator', width: 100,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') return '-';
        return getRel(r).creator_name || '-';
      },
    },
    { title: '审批步骤', dataIndex: 'step_name', key: 'step_name', width: 120 },
    { title: '发起时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
    {
      title: '操作', key: 'action', width: 140,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button type="primary" size="small" icon={<CheckOutlined />}
            onClick={() => handleApprove(record, 'approved')}>
            通过
          </Button>
          <Button danger size="small" icon={<CloseOutlined />}
            onClick={() => handleApprove(record, 'rejected')}>
            驳回
          </Button>
        </Space>
      ),
    },
  ];

  const historyColumns = [
    {
      title: '类型', key: 'approval_type', width: 100,
      render: (_: any, r: any) => (
        <Tag color={APPROVAL_TYPE_COLORS[r.approval_type] || 'default'}>
          {APPROVAL_TYPE_LABELS[r.approval_type] || r.approval_type || '-'}
        </Tag>
      ),
    },
    {
      title: '发布单号', key: 'release_no', width: 180,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Text code>{`伸缩: ${d.app_name || '?'} → ${d.env_name || '?'}`}</Text>;
        }
        return <Text code>{getRel(r).release_no || r.release_no || '-'}</Text>;
      },
    },
    {
      title: '应用', key: 'app', width: 140,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') return (r.extra_data || {}).app_name || '-';
        return getRel(r).application_name || '-';
      },
    },
    {
      title: '环境', key: 'env', width: 100,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Tag color={ENV_COLORS[d.env_code] || 'default'}>{d.env_name || '-'}</Tag>;
        }
        const code = getRel(r).environment_code || '';
        return <Tag color={ENV_COLORS[code] || 'default'}>{getRel(r).environment_name || '-'}</Tag>;
      },
    },
    {
      title: '详情', key: 'detail', width: 160,
      render: (_: any, r: any) => {
        if (r.approval_type === 'scale') {
          const d = r.extra_data || {};
          return <Text type="secondary">{d.current_replicas} → {d.target_replicas} ({d.action_label || '-'})</Text>;
        }
        const rel = getRel(r);
        return <Text type="secondary">版本: {rel.version || '-'}</Text>;
      },
    },
    { title: '审批步骤', dataIndex: 'step_name', key: 'step_name', width: 120 },
    {
      title: '结果', dataIndex: 'action', key: 'action', width: 90,
      render: (v: string) => <Tag color={STATUS_COLORS[v]}>{STATUS_LABELS[v] || v}</Tag>,
    },
    { title: '意见', dataIndex: 'comment', key: 'comment', width: 200, render: (v: string) => v || '-' },
    { title: '审批时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: any, record: any) => {
        const rid = getRel(record).id;
        return rid ? <Button type="link" size="small" onClick={() => navigate(`/releases/${rid}`)}>查看发布</Button> : '-';
      },
    },
  ];

  return (
    <div>
      <Title level={4}>发布审批</Title>
      <Tabs defaultActiveKey="pending" items={[
        {
          key: 'pending',
          label: `待审批 (${pendingList.length})`,
          children: (
            <Table
              dataSource={pendingList}
              columns={pendingColumns}
              rowKey="id"
              loading={pendingLoading}
              pagination={{ showTotal: (t) => `共 ${t} 条` }}
              locale={{ emptyText: '暂无待审批的发布单 🎉' }}
            />
          ),
        },
        {
          key: 'history',
          label: '审批记录',
          children: (
            <Table
              dataSource={historyList}
              columns={historyColumns}
              rowKey="id"
              loading={historyLoading}
              pagination={{ showTotal: (t) => `共 ${t} 条` }}
              locale={{ emptyText: '暂无审批记录' }}
            />
          ),
        },
      ]} />

      <Modal
        title={actionType === 'approved' ? '✅ 确认通过' : '❌ 确认驳回'}
        open={actionModalVisible}
        onOk={confirmAction}
        onCancel={() => setActionModalVisible(false)}
        okText={actionType === 'approved' ? '确认通过' : '确认驳回'}
        okButtonProps={{ danger: actionType === 'rejected' }}
        confirmLoading={actionSubmitting}
      >
        {selectedApproval && (
          <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="发布单">{getRel(selectedApproval).release_no || '-'}</Descriptions.Item>
            <Descriptions.Item label="应用">{getRel(selectedApproval).application_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="环境">{getRel(selectedApproval).environment_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="版本">{getRel(selectedApproval).version || '-'}</Descriptions.Item>
            <Descriptions.Item label="步骤">{selectedApproval.step_name}</Descriptions.Item>
          </Descriptions>
        )}
        <TextArea
          rows={3}
          placeholder={actionType === 'approved' ? '审批意见（选填）' : '驳回原因（建议填写）'}
          value={actionComment}
          onChange={(e) => setActionComment(e.target.value)}
        />
      </Modal>
    </div>
  );
}
