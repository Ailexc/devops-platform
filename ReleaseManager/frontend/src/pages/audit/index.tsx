import { useEffect, useState } from 'react';
import { Table, Select, Tag, Typography, Space } from 'antd';
import { auditApi } from '../../api';

const { Title, Text } = Typography;

interface AuditLog {
  id: number;
  user: string;
  action: string;
  resource_type: string;
  resource_id: string;
  detail: any;
  created_at: string;
}

const ACTION_COLORS: Record<string, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  submit: 'purple',
  approve: 'cyan',
  reject: 'orange',
  rollback: 'gold',
  login: 'default',
};

const ACTION_LABELS: Record<string, string> = {
  create: '创建',
  update: '更新',
  delete: '删除',
  submit: '提交',
  approve: '通过',
  reject: '驳回',
  rollback: '回滚',
  login: '登录',
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string | undefined>(undefined);
  const [actionFilter, setActionFilter] = useState<string | undefined>(undefined);

  // Collect unique resource types and actions from data for filter options
  const [resourceTypeOptions, setResourceTypeOptions] = useState<string[]>([]);
  const [actionOptions, setActionOptions] = useState<string[]>([]);

  const fetchLogs = () => {
    setLoading(true);
    auditApi.list().then((res: any) => {
      const data = res.data || [];
      let filtered = data;

      if (resourceTypeFilter) {
        filtered = filtered.filter((item: AuditLog) => item.resource_type === resourceTypeFilter);
      }
      if (actionFilter) {
        filtered = filtered.filter((item: AuditLog) => item.action === actionFilter);
      }

      setLogs(filtered);

      // Extract filter options from full data
      setResourceTypeOptions((prev: string[]) => {
        if (prev.length > 0) return prev;
        const types = new Set(data.map((item: AuditLog) => item.resource_type).filter(Boolean));
        return Array.from(types).sort() as string[];
      });
      setActionOptions((prev: string[]) => {
        if (prev.length > 0) return prev;
        const acts = new Set(data.map((item: AuditLog) => item.action).filter(Boolean));
        return Array.from(acts).sort() as string[];
      });
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [resourceTypeFilter, actionFilter]);

  const columns = [
    { title: '用户', dataIndex: 'user', key: 'user', width: 120 },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (v: string) => (
        <Tag color={ACTION_COLORS[v] || 'default'}>
          {ACTION_LABELS[v] || v}
        </Tag>
      ),
    },
    { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 120 },
    { title: '资源ID', dataIndex: 'resource_id', key: 'resource_id', width: 120 },
    {
      title: '详情',
      dataIndex: 'detail',
      key: 'detail',
      ellipsis: true,
      render: (v: any) => {
        if (!v) return '-';
        const str = typeof v === 'object' ? JSON.stringify(v) : String(v);
        return <Text code copyable style={{ fontSize: 12 }}>{str}</Text>;
      },
    },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>审计日志</Title>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="按资源类型筛选"
          allowClear
          style={{ width: 180 }}
          value={resourceTypeFilter}
          onChange={(value) => setResourceTypeFilter(value)}
          options={resourceTypeOptions.map((type) => ({
            value: type,
            label: type,
          }))}
        />
        <Select
          placeholder="按操作筛选"
          allowClear
          style={{ width: 180 }}
          value={actionFilter}
          onChange={(value) => setActionFilter(value)}
          options={actionOptions.map((act) => ({
            value: act,
            label: ACTION_LABELS[act] || act,
          }))}
        />
      </Space>

      <Table
        dataSource={logs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSize: 10,
        }}
        scroll={{ x: 900 }}
      />
    </div>
  );
}