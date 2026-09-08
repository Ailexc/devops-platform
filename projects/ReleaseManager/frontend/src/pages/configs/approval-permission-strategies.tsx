import { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag, Modal, Descriptions, Steps, Button } from 'antd';
import { LockOutlined, EyeOutlined } from '@ant-design/icons';
import { authzApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPE_LABELS: Record<string, string> = {
  dev: '开发', test: '测试', staging: '预发', prod: '生产',
};
const GRANT_SCOPE_LABELS: Record<string, string> = {
  own_group: '本组权限', cross_group: '跨组协作',
};
const APPROVER_RESOLVER_LABELS: Record<string, string> = {
  app_owner: '应用负责人', group_leader: '组负责人',
  business_line_leader: '业务线负责人', fixed_user: '固定人员',
  fixed_role: '固定角色组', parent_group_leader: '上级组负责人',
  security_team: '安全团队', ops_team: '运维团队',
};

export default function ApprovalPermissionStrategiesPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailTemplate, setDetailTemplate] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await authzApi.approvalConfigs.list();
      setConfigs(res.data || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const viewTemplateDetail = async (config: any) => {
    if (!config.flow_template) return;
    try {
      const res = await authzApi.approvalFlowTemplates.detail(config.flow_template);
      setDetailTemplate(res.data);
    } catch { /* ignore */ }
  };

  const columns = [
    {
      title: '环境类型', dataIndex: 'env_type', key: 'env_type', width: 100,
      render: (v: string) => <Tag color={v === 'prod' ? 'red' : v === 'staging' ? 'orange' : v === 'test' ? 'blue' : 'green'}>{ENV_TYPE_LABELS[v] || v}</Tag>,
    },
    {
      title: '授权范围', dataIndex: 'grant_scope', key: 'grant_scope', width: 100,
      render: (v: string) => GRANT_SCOPE_LABELS[v] || v,
    },
    {
      title: '是否需要审批', dataIndex: 'requires_approval', key: 'requires_approval', width: 100,
      render: (v: boolean) => v ? <Tag color="orange">需要审批</Tag> : <Tag color="green">自动通过</Tag>,
    },
    {
      title: '审批流模板', dataIndex: 'flow_template_name', key: 'flow_template', width: 200,
      render: (v: string, record: any) => v ? (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => viewTemplateDetail(record)}>
          {v}
        </Button>
      ) : '-',
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => v ? <Tag color="green">启用</Tag> : <Tag color="default">停用</Tag>,
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        <LockOutlined style={{ marginRight: 8, color: '#999' }} />
        权限策略
      </Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        按环境类型 + 授权范围配置权限审批策略。此配置为系统基线，仅支持查看。
      </Text>
      <Card size="small">
        <Table dataSource={configs} columns={columns} rowKey="id" loading={loading}
          pagination={false} size="small" locale={{ emptyText: '暂无权限策略配置' }} />
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
              <Tag>{detailTemplate.category === 'permission' ? '权限审批' : '发布审批'}</Tag>
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
