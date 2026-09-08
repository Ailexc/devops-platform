import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card, Form, Select, Button, Input, Radio, Checkbox, message, Typography,
  Space, Steps, Alert, Divider, Tag,
} from 'antd';
import { ArrowLeftOutlined, PlusOutlined } from '@ant-design/icons';
import { orgApi, appApi, infraApi, authzApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPES = [
  { value: 'dev', label: '开发', color: 'green' },
  { value: 'test', label: '测试', color: 'blue' },
  { value: 'staging', label: '预发', color: 'orange' },
  { value: 'prod', label: '生产', color: 'red' },
];

const ENV_TYPE_MAP = Object.fromEntries(ENV_TYPES.map((e) => [e.value, e]));

interface TreeUser {
  id: number;
  name: string;
  code: string;
  membership_type: string;
}

export default function PermissionApplyCollaborationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const currentGroupId = Number(searchParams.get('groupId')) || 0;

  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [approvalFlow, setApprovalFlow] = useState<any>(null);

  const [apps, setApps] = useState<any[]>([]);
  const [envs, setEnvs] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [businessLines, setBusinessLines] = useState<any[]>([]);
  const [treeData, setTreeData] = useState<any[]>([]);

  const [recipientType, setRecipientType] = useState<'group' | 'members'>('group');

  const currentGroup = useMemo(() => {
    return groups.find((g) => g.id === currentGroupId);
  }, [groups, currentGroupId]);

  const currentGroupMembers = useMemo<{ id: number; name: string; username: string; membership_type: string }[]>(() => {
    for (const bl of treeData) {
      for (const g of bl.children || []) {
        if (g.id === currentGroupId) {
          return (g.children || []).map((u: TreeUser) => ({
            id: u.id,
            name: u.name,
            username: u.code,
            membership_type: u.membership_type,
          }));
        }
      }
    }
    return [];
  }, [treeData, currentGroupId]);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [appRes, envRes, groupRes, blRes, treeRes] = await Promise.all([
        appApi.list(),
        infraApi.environments.list(),
        orgApi.groups.list(),
        orgApi.businessLines.list(),
        orgApi.tree(),
      ]);
      setApps(Array.isArray(appRes) ? appRes : (appRes?.data || []));
      setEnvs(Array.isArray(envRes) ? envRes : (envRes?.data || []));
      setGroups(groupRes?.data || []);
      setBusinessLines(blRes?.data || []);
      setTreeData(treeRes?.data || []);
    } catch {
      message.error('加载基础数据失败');
    }
  };

  const envType = Form.useWatch('env_type', form);
  const selectedAppId = Form.useWatch('app_id', form);
  const ownerBusinessLineId = Form.useWatch('owner_business_line_id', form);
  const ownerGroupId = Form.useWatch('owner_group_id', form);

  const envOptions = useMemo(() => {
    if (!envType) return [];
    return envs
      .filter((e) => e.env_type === envType)
      .map((e) => ({ label: e.name, value: e.id }));
  }, [envs, envType]);

  const availableOwnerGroups = useMemo(() => {
    return groups
      .filter((g) => g.id !== currentGroupId)
      .filter((g) => !ownerBusinessLineId || g.business_line === ownerBusinessLineId || g.business_line_id === ownerBusinessLineId);
  }, [groups, currentGroupId, ownerBusinessLineId]);

  const availableApps = useMemo(() => {
    if (!ownerGroupId) return [];
    return apps.filter((a) => a.owner_group === ownerGroupId);
  }, [apps, ownerGroupId]);

  const selectedApp = useMemo(() => availableApps.find((a) => a.id === selectedAppId), [availableApps, selectedAppId]);

  const handleEnvTypeChange = () => {
    form.setFieldsValue({ env_ids: [] });
    setApprovalFlow(null);
    setCurrentStep(1);
  };

  const handlePreviewApproval = async () => {
    const values = form.getFieldsValue();
    if (!values.app_id || !values.env_type) {
      message.warning('请先选择应用和环境类型');
      return;
    }
    setPreviewLoading(true);
    try {
      const res = await authzApi.calculateApprovalFlow({
        app_id: values.app_id,
        env_type: values.env_type,
        grant_scope: 'cross_group',
      });
      setApprovalFlow(res.data);
      setCurrentStep(2);
    } catch {
      message.error('计算审批流失败');
    } finally {
      setPreviewLoading(false);
    }
  };

  const validateRecipients = (values: any) => {
    if (recipientType === 'members') {
      if (!values.target_user_ids || values.target_user_ids.length === 0) {
        message.warning('请至少选择一个成员');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (!validateRecipients(values)) return;

    setLoading(true);
    try {
      const payload: any = {
        request_type: 'apply',
        app_id: values.app_id,
        env_type: values.env_type,
        is_all_envs: values.is_all_envs || false,
        env_ids: values.is_all_envs ? [] : (values.env_ids || []),
        grant_scope: 'cross_group',
        reason: values.reason,
        extra_data: {
          owner_group_id: values.owner_group_id,
        },
      };

      if (recipientType === 'group') {
        payload.extra_data.target_group_id = currentGroupId;
      } else {
        payload.extra_data.target_user_ids = values.target_user_ids;
      }

      await authzApi.permissionRequests.create(payload);
      message.success('协作应用申请已提交');
      navigate('/permissions');
    } catch {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  const recipientSection = (
    <div>
      <Divider>申请对象</Divider>
      <Form.Item
        name="owner_business_line_id"
        label="被申请业务线"
        rules={[{ required: true, message: '请选择被申请业务线' }]}
      >
        <Select
          showSearch
          placeholder="选择被申请业务线"
          optionFilterProp="label"
          options={businessLines.map((bl) => ({
            value: bl.id,
            label: bl.name,
          }))}
          onChange={() => form.setFieldsValue({ owner_group_id: undefined, app_id: undefined })}
        />
      </Form.Item>

      <Form.Item
        name="owner_group_id"
        label="被申请组（应用归属组）"
        rules={[{ required: true, message: '请选择被申请组' }]}
      >
        <Select
          showSearch
          placeholder="选择拥有该应用权限的组"
          optionFilterProp="label"
          disabled={!ownerBusinessLineId}
          options={availableOwnerGroups.map((g) => ({
            value: g.id,
            label: `${g.name}${g.business_line_name ? ` (${g.business_line_name})` : ''}`,
          }))}
          onChange={() => form.setFieldsValue({ app_id: undefined })}
        />
      </Form.Item>

      <Form.Item label="接收方式">
        <Radio.Group
          value={recipientType}
          onChange={(e) => {
            setRecipientType(e.target.value);
            form.setFieldsValue({ target_user_ids: [] });
          }}
        >
          <Radio.Button value="group">申请给当前组</Radio.Button>
          <Radio.Button value="members">申请给当前组成员</Radio.Button>
        </Radio.Group>
      </Form.Item>

      {recipientType === 'members' && (
        <Form.Item
          name="target_user_ids"
          label="指定成员"
          rules={[{ required: true, message: '请至少选择一个成员' }]}
        >
          <Checkbox.Group options={currentGroupMembers.map((u) => ({ label: u.name, value: u.id }))} />
        </Form.Item>
      )}
    </div>
  );

  const appEnvSection = (
    <div>
      <Divider>应用与环境</Divider>
      <Form.Item
        name="app_id"
        label="选择应用"
        rules={[{ required: true, message: '请选择应用' }]}
        extra={ownerGroupId && availableApps.length === 0 ? '该组下暂无可申请的应用' : undefined}
      >
        <Select
          showSearch
          placeholder="搜索被申请组下的应用"
          optionFilterProp="label"
          disabled={!ownerGroupId}
          options={availableApps.map((a) => ({
            value: a.id,
            label: `${a.name} (${a.code})`,
          }))}
        />
      </Form.Item>

      <Form.Item
        name="env_type"
        label="环境类型"
        rules={[{ required: true, message: '请选择环境类型' }]}
      >
        <Radio.Group onChange={handleEnvTypeChange}>
          {ENV_TYPES.map((et) => (
            <Radio.Button key={et.value} value={et.value}>
              <Tag color={et.color} style={{ marginRight: 4 }}>{et.label}</Tag>
            </Radio.Button>
          ))}
        </Radio.Group>
      </Form.Item>

      <Form.Item name="is_all_envs" label="全部环境" initialValue={false}>
        <Radio.Group>
          <Radio value={false}>选择具体环境</Radio>
          <Radio value={true}>该类型下全部环境</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prev, cur) => prev.is_all_envs !== cur.is_all_envs}
      >
        {({ getFieldValue }) => {
          const isAllEnvs = getFieldValue('is_all_envs');
          if (isAllEnvs) return null;
          return (
            <Form.Item
              name="env_ids"
              label="具体环境"
              rules={[{ required: true, message: '请至少选择一个环境' }]}
            >
              <Checkbox.Group options={envOptions} />
            </Form.Item>
          );
        }}
      </Form.Item>
    </div>
  );

  const approvalPreviewSection = approvalFlow && (
    <div>
      <Divider>审批链路预览</Divider>
      {approvalFlow.requires_approval ? (
        <>
          <Alert
            type="warning"
            title={`审批流模板: ${approvalFlow.flow_template_name}，预计耗时: ${approvalFlow.estimated_time || '-'}`}
            style={{ marginBottom: 12 }}
          />
          <Steps
            direction="vertical"
            size="small"
            current={-1}
            items={approvalFlow.steps.map((step: any) => ({
              title: step.name,
              description: (
                <div>
                  <div>
                    审批人: {step.approvers?.map((a: any) => a.name).join(', ') || '待定'}
                  </div>
                  <div style={{ color: '#888' }}>
                    需 {step.required_count || 1} 人审批 · 超时 {step.timeout_hours || 24}h
                  </div>
                </div>
              ),
            }))}
          />
        </>
      ) : (
        <Alert type="success" title="该环境类型无需审批，权限将直接生效" />
      )}

      <Form.Item
        name="reason"
        label="申请原因"
        style={{ marginTop: 16 }}
        rules={[{ required: true, message: '请填写申请原因' }]}
      >
        <Input.TextArea rows={3} placeholder="请说明申请原因" />
      </Form.Item>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <PlusOutlined style={{ marginRight: 8 }} />
          申请协作应用
        </Title>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/permissions')}>
          返回组织权限
        </Button>
      </div>

      <Card size="small">
        <Steps
          current={currentStep}
          size="small"
          style={{ marginBottom: 24 }}
          items={[
            { title: '选择申请对象' },
            { title: '选择应用环境' },
            { title: '预览审批流' },
            { title: '提交申请' },
          ]}
        />

        {currentGroup && (
          <Alert
            type="info"
            showIcon
            title={`当前操作组: ${currentGroup.name}`}
            description="申请通过后，当前组或成员将获得被申请组应用的协作权限。"
            style={{ marginBottom: 16 }}
          />
        )}

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <div style={{ display: currentStep >= 0 ? 'block' : 'none' }}>
            {recipientSection}
          </div>

          <div style={{ display: currentStep >= 1 ? 'block' : 'none' }}>
            {appEnvSection}
          </div>

          <div style={{ display: currentStep >= 2 ? 'block' : 'none' }}>
            {approvalPreviewSection}
          </div>

          <Space style={{ marginTop: 16 }}>
            {currentStep === 0 && (
              <Button type="primary" onClick={() => setCurrentStep(1)}>
                下一步：选择应用环境
              </Button>
            )}
            {currentStep === 1 && (
              <Button type="primary" onClick={handlePreviewApproval} loading={previewLoading}>
                预览审批流
              </Button>
            )}
            {currentStep === 2 && (
              <Button type="primary" htmlType="submit" loading={loading} icon={<PlusOutlined />}>
                提交申请
              </Button>
            )}
            {currentStep > 0 && (
              <Button onClick={() => setCurrentStep(currentStep - 1)}>
                上一步
              </Button>
            )}
            <Button onClick={() => { form.resetFields(); setCurrentStep(0); setApprovalFlow(null); }}>
              重置
            </Button>
          </Space>
        </Form>
      </Card>

      {selectedApp && (
        <Card size="small" style={{ marginTop: 16 }} title="已选应用">
          <Space>
            <Text strong>{selectedApp.name}</Text>
            <Tag>{selectedApp.code}</Tag>
            {envType && (
              <Tag color={ENV_TYPE_MAP[envType]?.color || 'default'}>
                {ENV_TYPE_MAP[envType]?.label}
              </Tag>
            )}
          </Space>
        </Card>
      )}
    </div>
  );
}
