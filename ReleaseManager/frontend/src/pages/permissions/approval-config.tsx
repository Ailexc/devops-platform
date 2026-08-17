import { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag, Space, Modal, Descriptions, Steps, Button } from 'antd';
import { LockOutlined, EyeOutlined } from '@ant-design/icons';
import { authzApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPE_LABELS: Record<string, string> = {
  dev: '开发', test: '测试', staging: '预发', prod: '生产',
};

const ENV_TYPE_COLORS: Record<string, string> = {
  dev: 'green', test: 'blue', staging: 'orange', prod: 'red',
};

const GRANT_SCOPE_LABELS: Record<string, string> = {
  own_group: '本组权限',
  cross_group: '跨组协作',
};

const APPROVER_RESOLVER_LABELS: Record<string, string> = {
  app_owner: '应用负责人',
  group_leader: '组负责人',
  business_line_leader: '业务线负责人',
  fixed_user: '固定人员',
  fixed_role: '固定角色组',
  parent_group_leader: '上级组负责人',
  security_team: '安全团队',
  ops_team: '运维团队',
};

export default function ApprovalConfigPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailTemplate, setDetailTemplate] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [configRes, templateRes] = await Promise.all([
        authzApi.approvalConfigs.list(),
        authzApi.approvalFlowTemplates.list(),
      ]);
      setConfigs(configRes.data || []);
      setTemplates(templateRes.data || []);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const configColumns = [
    {
      title: '环境类型', dataIndex: 'env_type', key: 'env_type', width: 100,
      render: (v: string) => <Tag color={ENV_TYPE_COLORS[v] || 'default'}>{ENV_TYPE_LABELS[v] || v}</Tag>,
    },
    {
      title: '授权范围', dataIndex: 'grant_scope', key: 'grant_scope', width: 100,
      render: (v: string) => (
        <Tag color={v === 'cross_group' ? 'orange' : 'blue'}>{GRANT_SCOPE_LABELS[v] || v}</Tag>
      ),
    },
    {
      title: '需要审批', dataIndex: 'requires_approval', key: 'requires', width: 100,
      render: (v: boolean) => <Tag color={v ? 'red' : 'green'}>{v ? '是' : '否'}</Tag>,
    },
    {
      title: '审批流模板', dataIndex: 'flow_template_name', key: 'template',
      render: (v: string) => v ? <Tag color="blue">{v}</Tag> : <Text type="secondary">未设置</Text>,
    },
  ];

  const templateColumns = [
    { title: '模板名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '步骤数', key: 'steps', width: 80,
      render: (_: any, record: any) => (record.steps || []).length,
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag>,
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
      <div style={{ marginBottom: 16, padding: '8px 16px', background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 6 }}>
        <Space>
          <LockOutlined style={{ color: '#faad14' }} />
          <Text type="secondary">
            审批配置为系统基线配置，不可编辑。如需修改请通过代码部署更新。
          </Text>
        </Space>
      </div>

      <Title level={4}>审批配置</Title>

      {/* 审批策略 */}
      <Card title="审批策略" size="small" style={{ marginBottom: 16 }}>
        <Table
          dataSource={configs}
          columns={configColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>

      {/* 审批流模板 */}
      <Card title="审批流模板" size="small">
        <Table
          dataSource={templates}
          columns={templateColumns}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Card>

      {/* 审批流模板详情弹窗（只读） */}
      <Modal
        title={detailTemplate?.name || '审批流模板详情'}
        open={!!detailTemplate}
        onCancel={() => setDetailTemplate(null)}
        footer={null}
        width={640}
      >
        {detailTemplate && (
          <div>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 20 }}>
              <Descriptions.Item label="模板名称">{detailTemplate.name}</Descriptions.Item>
              <Descriptions.Item label="编码">{detailTemplate.code}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{detailTemplate.description || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态" span={2}>
                <Tag color={detailTemplate.is_active ? 'green' : 'default'}>
                  {detailTemplate.is_active ? '启用' : '停用'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <Title level={5} style={{ marginBottom: 12 }}>审批步骤</Title>

            {(detailTemplate.steps || []).length === 0 ? (
              <Text type="secondary">暂无审批步骤</Text>
            ) : (
              <Steps
                orientation="vertical"
                size="small"
                current={-1}
                items={(detailTemplate.steps || []).map((step: any, i: number) => ({
                  title: `第 ${step.order || i + 1} 步: ${step.name}`,
                  description: (
                    <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
                      <Tag>
                        {APPROVER_RESOLVER_LABELS[step.approver_resolver] || step.approver_resolver || '未指定'}
                      </Tag>
                      <span style={{ marginLeft: 8 }}>
                        需 {step.required_count || 1} 人审批
                        {step.timeout_hours ? ` · ${step.timeout_hours} 小时超时` : ''}
                      </span>
                    </div>
                  ),
                }))}
              />
            )}

            <div style={{ marginTop: 20, padding: '8px 12px', background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 6 }}>
              <Space>
                <LockOutlined style={{ color: '#faad14', fontSize: 12 }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  此模板为系统基线配置，不可编辑
                </Text>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
