import { useEffect, useState, useCallback } from 'react';
import {
  Table, Tag, Typography, Space, Button, Modal, Input, message, Tabs, Descriptions,
} from 'antd';
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { approvalApi } from '../../api';

const { Text } = Typography;
const { TextArea } = Input;

const STATUS_LABELS: Record<string, string> = {
  pending: '待审批', approved: '已通过', rejected: '已驳回',
};

const REQUEST_TYPE_LABELS: Record<string, string> = {
  share: '分享协作',
  revoke: '回收权限',
  release: '解除协作',
};
const REQUEST_TYPE_COLORS: Record<string, string> = {
  share: 'blue', revoke: 'orange', release: 'red',
};

export default function ChangeApprovalPage() {
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
    approvalApi.changePending().then((res: any) => {
      setPendingList(res.data || []);
    }).finally(() => setPendingLoading(false));
  }, []);

  const fetchHistory = useCallback(() => {
    setHistoryLoading(true);
    approvalApi.changeList().then((res: any) => {
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
        ? () => approvalApi.approveStep(selectedApproval.id, actionComment)
        : () => approvalApi.rejectStep(selectedApproval.id, actionComment);
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

  const renderStep = (r: any) => {
    if (r.step_order && r.total_steps && r.total_steps > 1) {
      return (
        <Text type="secondary">
          第 {r.step_order}/{r.total_steps} 步
          {r.step_name && <span> · {r.step_name}</span>}
        </Text>
      );
    }
    return <Text type="secondary">-</Text>;
  };

  const renderRequestType = (r: any) => {
    const reqType = r.request_type || 'share';
    return (
      <Tag color={REQUEST_TYPE_COLORS[reqType] || 'default'}>
        {REQUEST_TYPE_LABELS[reqType] || reqType}
      </Tag>
    );
  };

  const pendingColumns = [
    {
      title: '申请人', dataIndex: 'applicant_name', key: 'applicant_name', width: 100,
      render: (v: string) => <Text strong>{v || '-'}</Text>,
    },
    {
      title: '应用', dataIndex: 'app_name', key: 'app_name', width: 140,
      render: (v: string) => <Text strong>{v || '-'}</Text>,
    },
    {
      title: '变更类型', key: 'request_type', width: 110,
      render: (_: any, r: any) => renderRequestType(r),
    },
    {
      title: '审批步骤', key: 'step', width: 150,
      render: (_: any, r: any) => renderStep(r),
    },
    {
      title: '审批人', dataIndex: 'approver_name', key: 'approver_name', width: 100,
    },
    {
      title: '申请时间', dataIndex: 'created_at', key: 'created_at', width: 160,
    },
    {
      title: '操作', key: 'action', width: 160,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button type="link" style={{ color: '#52c41a' }} size="small" icon={<CheckOutlined />}
            onClick={() => handleApprove(record, 'approved')}>通过</Button>
          <Button type="link" danger size="small" icon={<CloseOutlined />}
            onClick={() => handleApprove(record, 'rejected')}>驳回</Button>
        </Space>
      ),
    },
  ];

  const historyColumns = [
    {
      title: '申请人', dataIndex: 'applicant_name', key: 'applicant_name', width: 100,
      render: (v: string) => <Text strong>{v || '-'}</Text>,
    },
    {
      title: '应用', dataIndex: 'app_name', key: 'app_name', width: 140,
      render: (v: string) => <Text strong>{v || '-'}</Text>,
    },
    {
      title: '变更类型', key: 'request_type', width: 110,
      render: (_: any, r: any) => renderRequestType(r),
    },
    {
      title: '审批步骤', key: 'step', width: 150,
      render: (_: any, r: any) => renderStep(r),
    },
    {
      title: '结果', dataIndex: 'action', key: 'action_result', width: 90,
      render: (v: string) => {
        const color = v === 'approved' ? 'green' : v === 'rejected' ? 'red' : 'orange';
        return <Tag color={color}>{STATUS_LABELS[v] || v}</Tag>;
      },
    },
    {
      title: '意见', dataIndex: 'comment', key: 'comment', ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '时间', dataIndex: 'updated_at', key: 'updated_at', width: 160,
    },
  ];

  const tabItems = [
    {
      key: 'pending',
      label: `我的待审批 (${pendingList.length})`,
      children: (
        <Table dataSource={pendingList} columns={pendingColumns} rowKey="id"
          loading={pendingLoading} pagination={{ showSizeChanger: true, showQuickJumper: true, showTotal: (t) => `共 ${t} 条`, pageSize: 10 }}
          scroll={{ x: 900 }}
        />
      ),
    },
    {
      key: 'history',
      label: '审批历史',
      children: (
        <Table dataSource={historyList} columns={historyColumns} rowKey="id"
          loading={historyLoading} pagination={{ showSizeChanger: true, showQuickJumper: true, showTotal: (t) => `共 ${t} 条`, pageSize: 10 }}
          scroll={{ x: 900 }}
        />
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}>变更审批</Typography.Title>
      <Tabs items={tabItems} />

      <Modal
        title={actionType === 'approved' ? '确认通过' : '确认驳回'}
        open={actionModalVisible}
        onOk={confirmAction}
        onCancel={() => setActionModalVisible(false)}
        okText={actionType === 'approved' ? '通过' : '驳回'}
        okButtonProps={{ danger: actionType === 'rejected', loading: actionSubmitting }}
      >
        {selectedApproval && (
          <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
            <Descriptions.Item label="申请人">{selectedApproval.applicant_name}</Descriptions.Item>
            <Descriptions.Item label="应用">{selectedApproval.app_name}</Descriptions.Item>
            <Descriptions.Item label="变更类型">{REQUEST_TYPE_LABELS[selectedApproval.request_type] || selectedApproval.request_type}</Descriptions.Item>
          </Descriptions>
        )}
        <TextArea rows={3} placeholder="审批意见（可选）" value={actionComment} onChange={(e) => setActionComment(e.target.value)} />
      </Modal>
    </div>
  );
}
