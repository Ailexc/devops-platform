import { useEffect, useState, useCallback } from 'react';
import {
  Drawer, Tabs, Card, Checkbox, Table, Tag, Button, Space, message,
  Typography, Divider, Spin, Empty, Popconfirm, Steps, Alert,
} from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import { authzApi } from '../../api';

const { Text, Title } = Typography;

interface EnvInfo {
  id: number;
  name: string;
  code: string;
  env_type: string;
  cloud_provider?: string;
  account_id?: string;
  region?: string;
  zone?: string;
}

interface MemberItem {
  user_id: number;
  user_name: string;
  username: string;
  membership_type: string;
  is_leader: boolean;
  role_name: string;
  allowed_env_ids: number[];
  allowed_env_names: string[];
  permission_source: string;
}

interface ExternalUserItem {
  user_id: number;
  user_name: string;
  username: string;
  source_group_name: string;
  allowed_env_ids: number[];
  allowed_env_names: string[];
  created_at: string;
}

interface CollabGroupItem {
  group_id: number;
  group_name: string;
  group_code: string;
  sharer_name: string;
  allowed_env_ids: number[];
  allowed_env_names: string[];
  is_all_envs: boolean;
  created_at: string;
}

interface AdjustDetail {
  app_id: number;
  app_name: string;
  app_code: string;
  env_type: string;
  env_type_label: string;
  all_envs: EnvInfo[];
  members: MemberItem[];
  external_users: ExternalUserItem[];
  collab_groups: CollabGroupItem[];
}

interface ApprovalStep {
  order: number;
  name: string;
  dimension: string;
  approver_resolver: string;
  approvers: { id: number; name: string }[];
  required_count: number;
  timeout_hours: number;
}

interface Props {
  open: boolean;
  groupId: number;
  appId: number;
  appName: string;
  envType: string;
  onClose: () => void;
  onSuccess: () => void;
}

const ENV_TYPE_TAG_COLORS: Record<string, string> = {
  dev: 'green', test: 'blue', staging: 'orange', prod: 'red',
};

const ENV_TYPE_LABELS: Record<string, string> = {
  dev: '开发', test: '测试', staging: '预发', prod: '生产',
};

const cloudProviderLabels: Record<string, string> = {
  aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', huawei: '华为云', azure: 'Azure', gcp: 'GCP',
};

export default function PermissionAdjustDrawer({
  open, groupId, appId, appName, envType, onClose, onSuccess,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AdjustDetail | null>(null);
  const [activeTab, setActiveTab] = useState('members');
  const [submitting, setSubmitting] = useState(false);

  // 变更追踪：记录每个 user/group 的当前选中 env_ids
  const [memberEnvSelections, setMemberEnvSelections] = useState<Record<number, Set<number>>>({});
  const [externalEnvSelections, setExternalEnvSelections] = useState<Record<number, Set<number>>>({});
  const [collabEnvSelections, setCollabEnvSelections] = useState<Record<number, Set<number>>>({});

  // 审批链预览
  const [approvalFlow, setApprovalFlow] = useState<{
    requires_approval: boolean;
    steps: ApprovalStep[];
    flow_template_name: string;
    estimated_time: string;
  } | null>(null);
  const [flowLoading, setFlowLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!groupId || !appId || !envType) return;
    setLoading(true);
    try {
      const res = await authzApi.adjustDetail(groupId, appId, envType);
      const detail: AdjustDetail = res.data;
      setData(detail);

      // 初始化选中状态
      const mSel: Record<number, Set<number>> = {};
      detail.members.forEach((m) => { mSel[m.user_id] = new Set(m.allowed_env_ids); });
      setMemberEnvSelections(mSel);

      const eSel: Record<number, Set<number>> = {};
      detail.external_users.forEach((u) => { eSel[u.user_id] = new Set(u.allowed_env_ids); });
      setExternalEnvSelections(eSel);

      const cSel: Record<number, Set<number>> = {};
      detail.collab_groups.forEach((g) => { cSel[g.group_id] = new Set(g.allowed_env_ids); });
      setCollabEnvSelections(cSel);
    } catch {
      message.error('加载权限调整详情失败');
    } finally {
      setLoading(false);
    }
  }, [groupId, appId, envType]);

  const loadApprovalFlow = useCallback(async () => {
    if (!appId || !envType) return;
    setFlowLoading(true);
    try {
      const res = await authzApi.calculateApprovalFlow({
        app_id: appId,
        env_type: envType,
        grant_scope: 'own_group',
      });
      setApprovalFlow(res.data);
    } catch {
      // ignore
    } finally {
      setFlowLoading(false);
    }
  }, [appId, envType]);

  useEffect(() => {
    if (open) {
      loadData();
      loadApprovalFlow();
    }
  }, [open, loadData, loadApprovalFlow]);

  const handleMemberToggle = (userId: number, envId: number, checked: boolean) => {
    setMemberEnvSelections((prev) => {
      const next = { ...prev };
      const s = new Set(next[userId] || []);
      if (checked) s.add(envId); else s.delete(envId);
      next[userId] = s;
      return next;
    });
  };

  const handleExternalToggle = (userId: number, envId: number, checked: boolean) => {
    setExternalEnvSelections((prev) => {
      const next = { ...prev };
      const s = new Set(next[userId] || []);
      if (checked) s.add(envId); else s.delete(envId);
      next[userId] = s;
      return next;
    });
  };

  const handleCollabToggle = (groupId: number, envId: number, checked: boolean) => {
    setCollabEnvSelections((prev) => {
      const next = { ...prev };
      const s = new Set(next[groupId] || []);
      if (checked) s.add(envId); else s.delete(envId);
      next[groupId] = s;
      return next;
    });
  };

  // 计算变更
  const computeChanges = () => {
    if (!data) return { member_changes: [], external_changes: [], collab_changes: [] };

    const memberChanges = data.members
      .map((m) => {
        const current = memberEnvSelections[m.user_id] || new Set();
        const original = new Set(m.allowed_env_ids);
        const add = [...current].filter((id) => !original.has(id));
        const remove = [...original].filter((id) => !current.has(id));
        return { user_id: m.user_id, add_env_ids: add, remove_env_ids: remove };
      })
      .filter((c) => c.add_env_ids.length > 0 || c.remove_env_ids.length > 0);

    const externalChanges = data.external_users
      .map((u) => {
        const current = externalEnvSelections[u.user_id] || new Set();
        const original = new Set(u.allowed_env_ids);
        const add = [...current].filter((id) => !original.has(id));
        const remove = [...original].filter((id) => !current.has(id));
        return { user_id: u.user_id, add_env_ids: add, remove_env_ids: remove };
      })
      .filter((c) => c.add_env_ids.length > 0 || c.remove_env_ids.length > 0);

    const collabChanges = data.collab_groups
      .map((g) => {
        const current = collabEnvSelections[g.group_id] || new Set();
        const original = new Set(g.allowed_env_ids);
        const add = [...current].filter((id) => !original.has(id));
        const remove = [...original].filter((id) => !current.has(id));
        return { group_id: g.group_id, add_env_ids: add, remove_env_ids: remove };
      })
      .filter((c) => c.add_env_ids.length > 0 || c.remove_env_ids.length > 0);

    return { member_changes: memberChanges, external_changes: externalChanges, collab_changes: collabChanges };
  };

  const handleSubmit = async () => {
    const changes = computeChanges();
    const totalChanges =
      changes.member_changes.length + changes.external_changes.length + changes.collab_changes.length;

    if (totalChanges === 0) {
      message.info('没有权限变更');
      return;
    }

    setSubmitting(true);
    try {
      await authzApi.adjustSubmit(groupId, {
        app_id: appId,
        env_type: envType,
        reason: `权限调整 - ${appName} ${ENV_TYPE_LABELS[envType] || envType}`,
        adjustments: changes,
      });
      message.success('权限调整申请已提交');
      onSuccess();
      onClose();
    } catch {
      message.error('提交失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 获取变更摘要
  const changes = computeChanges();
  const totalChanges =
    changes.member_changes.length + changes.external_changes.length + changes.collab_changes.length;
  const hasChanges = totalChanges > 0;

  const renderEnvCheckboxes = (
    allEnvs: EnvInfo[],
    selectedIds: Set<number>,
    originalIds: number[],
    onToggle: (envId: number, checked: boolean) => void,
  ) => {
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {allEnvs.map((env) => {
          const isSelected = selectedIds.has(env.id);
          const wasOriginal = originalIds.includes(env.id);
          const changed = isSelected !== wasOriginal;
          return (
            <Checkbox
              key={env.id}
              checked={isSelected}
              onChange={(e) => onToggle(env.id, e.target.checked)}
              style={{
                padding: '4px 8px',
                border: changed ? '1px solid #faad14' : '1px solid #d9d9d9',
                borderRadius: 4,
                background: changed ? '#fffbe6' : '#fff',
                marginRight: 0,
              }}
            >
              <span style={{ fontSize: 12 }}>
                {env.name}
                {changed && (
                  <Tag
                    color={isSelected ? 'green' : 'red'}
                    style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px' }}
                  >
                    {isSelected ? '新增' : '回收'}
                  </Tag>
                )}
              </span>
            </Checkbox>
          );
        })}
      </div>
    );
  };

  const renderMemberTab = () => {
    if (!data) return null;
    if (data.members.length === 0) return <Empty description="暂无组内成员" />;

    return (
      <div>
        {data.members.map((m) => {
          const selectedIds = memberEnvSelections[m.user_id] || new Set();
          return (
            <Card
              key={m.user_id}
              size="small"
              style={{ marginBottom: 12 }}
              title={
                <Space>
                  <Text strong>{m.user_name}</Text>
                  <Tag color="default" style={{ fontSize: 10 }}>{m.username}</Tag>
                  <Tag color={m.membership_type === 'primary' ? 'blue' : 'orange'}>
                    {m.role_name}
                  </Tag>
                  {m.permission_source === 'personal' && <Tag color="purple">个人权限</Tag>}
                  {m.permission_source === 'mixed' && <Tag color="magenta">混合权限</Tag>}
                  {m.permission_source === 'team' && <Tag color="blue">团队权限</Tag>}
                </Space>
              }
            >
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                当前已授权: {m.allowed_env_names.join(', ') || '无'}
              </Text>
              {renderEnvCheckboxes(
                data.all_envs,
                selectedIds,
                m.allowed_env_ids,
                (envId, checked) => handleMemberToggle(m.user_id, envId, checked),
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  const renderExternalTab = () => {
    if (!data) return null;
    if (data.external_users.length === 0) return <Empty description="暂无组外个人权限" />;

    return (
      <div>
        {data.external_users.map((u) => {
          const selectedIds = externalEnvSelections[u.user_id] || new Set();
          return (
            <Card
              key={u.user_id}
              size="small"
              style={{ marginBottom: 12 }}
              title={
                <Space>
                  <Text strong>{u.user_name}</Text>
                  <Tag color="default" style={{ fontSize: 10 }}>{u.username}</Tag>
                  <Tag color="orange">{u.source_group_name}</Tag>
                </Space>
              }
            >
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                当前已授权: {u.allowed_env_names.join(', ') || '无'} | 授权日期: {u.created_at}
              </Text>
              {renderEnvCheckboxes(
                data.all_envs,
                selectedIds,
                u.allowed_env_ids,
                (envId, checked) => handleExternalToggle(u.user_id, envId, checked),
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  const renderCollabTab = () => {
    if (!data) return null;
    if (data.collab_groups.length === 0) return <Empty description="暂无协作组权限" />;

    return (
      <div>
        {data.collab_groups.map((g) => {
          const selectedIds = collabEnvSelections[g.group_id] || new Set();
          return (
            <Card
              key={g.group_id}
              size="small"
              style={{ marginBottom: 12 }}
              title={
                <Space>
                  <Text strong>{g.group_name}</Text>
                  <Tag color="default" style={{ fontSize: 10 }}>{g.group_code}</Tag>
                  <Tag color="orange">协作组</Tag>
                  {g.is_all_envs && <Tag color="green">全部环境</Tag>}
                </Space>
              }
            >
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                当前已授权: {g.allowed_env_names.join(', ') || '无'} | 授权日期: {g.created_at}
              </Text>
              {renderEnvCheckboxes(
                data.all_envs,
                selectedIds,
                g.allowed_env_ids,
                (envId, checked) => handleCollabToggle(g.group_id, envId, checked),
              )}
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <Drawer
      title={
        <Space>
          <Text strong>权限调整</Text>
          <Tag color={ENV_TYPE_TAG_COLORS[envType] || 'default'}>
            {ENV_TYPE_LABELS[envType] || envType}
          </Tag>
          <Text type="secondary">{appName}</Text>
        </Space>
      }
      open={open}
      onClose={onClose}
      size="large"
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            {hasChanges && (
              <Space>
                <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                <Text style={{ color: '#faad14' }}>共 {totalChanges} 项变更待提交</Text>
              </Space>
            )}
          </div>
          <Space>
            <Button onClick={onClose}>取消</Button>
            <Popconfirm
              title="确认提交"
              description={
                <div>
                  <p>共 {totalChanges} 项权限变更，提交后将进入审批流程。</p>
                  {approvalFlow?.requires_approval && (
                    <p style={{ color: '#faad14' }}>
                      预计审批耗时: {approvalFlow.estimated_time || '待定'}
                    </p>
                  )}
                </div>
              }
              onConfirm={handleSubmit}
              okText="确认提交"
              cancelText="取消"
              disabled={!hasChanges}
            >
              <Button type="primary" loading={submitting} disabled={!hasChanges}>
                提交变更
              </Button>
            </Popconfirm>
          </Space>
        </div>
      }
    >
      <Spin spinning={loading}>
        {data && (
          <>
            {/* 环境概览 */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                环境列表: {data.all_envs.map((e) => (
                  <Tag key={e.id} color="default" style={{ margin: '0 2px' }}>
                    {e.name} ({cloudProviderLabels[e.cloud_provider || ''] || e.cloud_provider || '-'})
                  </Tag>
                ))}
              </Text>
            </Card>

            {/* 审批链预览 */}
            {approvalFlow && (
              <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
                <Text strong style={{ fontSize: 12 }}>
                  审批链预览: {approvalFlow.flow_template_name || '无需审批'}
                </Text>
                {approvalFlow.requires_approval && approvalFlow.steps.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    {approvalFlow.steps.map((step, idx) => (
                      <div key={idx} style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>
                        第{step.order}步: {step.name} —{' '}
                        {step.approvers.map((a) => a.name).join(', ') || '待定'}
                        {step.required_count > 1 && ` (需${step.required_count}人)`}
                      </div>
                    ))}
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      预计耗时: {approvalFlow.estimated_time}
                    </Text>
                  </div>
                )}
              </Card>
            )}

            {/* 三 Tab */}
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              size="small"
              items={[
                {
                  key: 'members',
                  label: `组内成员权限 (${data.members.length})`,
                  children: renderMemberTab(),
                },
                {
                  key: 'external',
                  label: `组外个人权限 (${data.external_users.length})`,
                  children: renderExternalTab(),
                },
                {
                  key: 'collab',
                  label: `协作组权限 (${data.collab_groups.length})`,
                  children: renderCollabTab(),
                },
              ]}
            />
          </>
        )}
      </Spin>
    </Drawer>
  );
}