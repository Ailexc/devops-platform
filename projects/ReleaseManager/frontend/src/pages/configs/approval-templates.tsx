import { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag, Modal, Descriptions, Steps, Button } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { authzApi } from '../../api';

const { Title, Text } = Typography;

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  release: { label: '发布审批', color: 'blue' },
  permission: { label: '权限审批', color: 'purple' },
  app_change: { label: '应用变更审批', color: 'orange' },
};

const APPROVER_RESOLVER_LABELS: Record<string, string> = {
  app_owner: '应用负责人', group_leader: '组负责人',
  business_line_leader: '业务线负责人', fixed_user: '固定人员',
  fixed_role: '固定角色组', parent_group_leader: '上级组负责人',
  security_team: '安全团队', ops_team: '运维团队',
};

export default function ApprovalTemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailTemplate, setDetailTemplate] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await authzApi.approvalFlowTemplates.list();
      setTemplates(res.data || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 160 },
    { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
    {
      title: '分类', dataIndex: 'category', key: 'category', width: 120,
      render: (v: string) => {
        const cfg = CATEGORY_LABELS[v] || { label: v, color: 'default' };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '步骤数', key: 'steps_count', width: 80,
      render: (_: any, record: any) => record.steps?.length || 0,
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => v ? <Tag color="green">启用</Tag> : <Tag color="default">停用</Tag>,
    },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: any, record: any) => (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setDetailTemplate(record)}>
          查看
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>审核模板</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        所有审批流模板的统一管理。模板为系统基线配置，不可修改。
      </Text>
      <Card size="small">
        <Table dataSource={templates} columns={columns} rowKey="id" loading={loading}
          pagination={false} size="small" locale={{ emptyText: '暂无审核模板' }} />
      </Card>

      <Modal title={`审批流模板: ${detailTemplate?.name || ''}`} open={!!detailTemplate}
        onCancel={() => setDetailTemplate(null)}
        footer={<Button onClick={() => setDetailTemplate(null)}>关闭</Button>} width={640}>
        {detailTemplate && (
          <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
            <Descriptions.Item label="名称">{detailTemplate.name}</Descriptions.Item>
            <Descriptions.Item label="编码">{detailTemplate.code}</Descriptions.Item>
            <Descriptions.Item label="描述">{detailTemplate.description || '无'}</Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color={(CATEGORY_LABELS[detailTemplate.category] || {}).color || 'default'}>
                {(CATEGORY_LABELS[detailTemplate.category] || {}).label || detailTemplate.category}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
        {detailTemplate?.steps?.length > 0 && (
          <Steps direction="vertical" current={-1}
            items={detailTemplate.steps.map((step: any, idx: number) => ({
              title: `${idx + 1}. ${step.name || '未命名步骤'}`,
              description: (
                <div style={{ fontSize: 13 }}>
                  <div>审批人: {APPROVER_RESOLVER_LABELS[step.approver_resolver] || step.approver_resolver || '-'}</div>
                  <div>最少通过数: {step.required_count ?? 1}</div>
                  {step.timeout_hours && <div>超时时间: {step.timeout_hours} 小时</div>}
                </div>
              ),
            }))} />
        )}
      </Modal>
    </div>
  );
}
