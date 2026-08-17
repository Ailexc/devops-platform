import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card, Form, Select, Button, Input, Radio, Checkbox, message, Typography,
  Space, Steps, Alert, Divider, Tag, Descriptions,
} from 'antd';
import { ArrowLeftOutlined, RollbackOutlined } from '@ant-design/icons';
import { orgApi, appApi, infraApi, authzApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPE_MAP: Record<string, { label: string; color: string }> = {
  dev: { label: '开发', color: 'green' },
  test: { label: '测试', color: 'blue' },
  staging: { label: '预发', color: 'orange' },
  prod: { label: '生产', color: 'red' },
};

export default function RevokePermissionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const groupId = Number(searchParams.get('groupId')) || 0;
  const appId = Number(searchParams.get('appId')) || 0;
  const envType = searchParams.get('envType') || '';

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
  const [currentGroup, setCurrentGroup] = useState<any>(null);

  const [recipientType, setRecipientType] = useState<'group' | 'members'>('group');

  const targetBusinessLineId = Form.useWatch('target_business_line_id', form);
  const targetGroupId = Form.useWatch('target_group_id', form);
  const selectedAppId = Form.useWatch('app_id', form);
  const selectedEnvType = Form.useWatch('env_type', form);

  useEffect(() => {
    loadInitialData();
    loadGroupInfo();
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

  const loadGroupInfo = async () => {
    if (!groupId) return;
    try {
      const res = await orgApi.groups.list();
      const groups = res?.data || [];
      setCurrentGroup(groups.find((g: any) => g.id === groupId) || null);
    } catch {
      // ignore
    }
  };

  const currentGroupApps = useMemo(() => {
    return apps.filter((a) => a.owner_group === groupId);
  }, [apps, groupId]);

  const envOptions = useMemo(() => {
    if (!selectedEnvType) return [];
    return envs
      .filter((e) => e.env_type === selectedEnvType)
      .map((e) => ({ label: e.name, value: e.id }));
  }, [envs, selectedEnvType]);

  const availableTargetGroups = useMemo(() => {
    return groups
      .filter((g) => g.id !== groupId)
      .filter((g) => !targetBusinessLineId || g.business_line === targetBusinessLineId || g.business_line_id === targetBusinessLineId);
  }, [groups, groupId, targetBusinessLineId]);

  const targetGroupMembers = useMemo(() => {
    if (!targetGroupId) return [];
    for (const bl of treeData) {
      for (const g of bl.children || []) {
        if (g.id === targetGroupId) {
          return (g.children || []).map((u: any) => ({
            id: u.id,
            name: u.name,
            username: u.code,
            membership_type: u.membership_type,
          }));
        }
      }
    }
    return [];
  }, [treeData, targetGroupId]);

  const selectedApp = useMemo(() => currentGroupApps.find((a) => a.id === selectedAppId), [currentGroupApps, selectedAppId]);

  const handleEnvTypeChange = () => {
    form.setFieldsValue({ env_ids: [] });
    setApprovalFlow(null);
    if (currentStep >= 2) setCurrentStep(1);
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
    if (recipientType === 'group') {
      if (!values.target_group_id) {
        message.warning('请选择目标组');
        return false;
      }
    } else {
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
        request_type: 'revoke',
        app_id: values.app_id,
        env_type: values.env_type,
        is_all_envs: values.is_all_envs || false,
        env_ids: values.is_all_envs ? [] : (values.env_ids || []),
        grant_scope: 'cross_group',
        reason: values.reason,
        extra_data: {
          owner_group_id: groupId,
        },
      };

      if (recipientType === 'group') {
        payload.extra_data.target_group_id = values.target_group_id;
      } else {
        payload.extra_data.target_user_ids = values.target_user_ids;
      }

      await authzApi.permissionRequests.create(payload);
      message.success('回收协作权限申请已提交');
      navigate('/permissions');
    } catch {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  const recipientSection = (
    <div>
      <Divider>回收对象</Divider>
      <Form.Item label="回收方式">
        <Radio.Group
          value={recipientType}
          onChange={(e) => {
            setRecipientType(e.target.value);
            form.setFieldsValue({ target_user_ids: [] });
          }}
        >
          <Radio.Button value="group">从其他组回收</Radio.Button>
          <Radio.Button value="members">从指定成员回收</Radio.Button>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        name="target_business_line_id"
        label="目标业务线"
        rules={[{ required: true, message: '请选择目标业务线' }]}
      >
        <Select
          showSearch
          placeholder="选择目标业务线"
          optionFilterProp="label"
          options={businessLines.map((bl) => ({
            value: bl.id,
            label: bl.name,
          }))}
          onChange={() => form.setFieldsValue({ target_group_id: undefined, target_user_ids: [] })}
        />
      </Form.Item>
      <Form.Item
        name="target_group_id"
        label="目标组"
        rules={[{ required: true, message: '请选择目标组' }]}
      >
        <Select
          showSearch
          placeholder="选择要回收权限的组"
          optionFilterProp="label"
          disabled={!targetBusinessLineId}
          options={availableTargetGroups.map((g) => ({
            value: g.id,
            label: `${g.name}${g.business_line_name ? ` (${g.business_line_name})` : ''}`,
          }))}
          onChange={() => form.setFieldsValue({ target_user_ids: [] })}
        />
      </Form.Item>

      {recipientType === 'members' && (
        <Form.Item
          name="target_user_ids"
          label="指定成员"
          rules={[{ required: true, message: '请至少选择一个成员' }]}
        >
          <Checkbox.Group
            disabled={!targetGroupId}
            options={targetGroupMembers.map((u) => ({ label: u.name, value: u.id }))}
          />
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
        initialValue={appId || undefined}
        extra={currentGroupApps.length === 0 ? '当前组暂无可回收权限的应用' : undefined}
      >
        <Select
          showSearch
          placeholder="搜索当前组下的应用"
          optionFilterProp="label"
          options={currentGroupApps.map((a) => ({
            value: a.id,
            label: `${a.name} (${a.code})`,
          }))}
        />
      </Form.Item>

      <Form.Item
        name="env_type"
        label="环境类型"
        rules={[{ required: true, message: '请选择环境类型' }]}
        initialValue={envType || undefined}
      >
        <Select onChange={handleEnvTypeChange}>
          {Object.entries(ENV_TYPE_MAP).map(([key, val]) => (
            <Select.Option key={key} value={key}>
              <Tag color={val.color}>{val.label}</Tag>
            </Select.Option>
          ))}
        </Select>
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
            title={`审批流模板: ${approvalFlow.flow_template_name || '默认审批流'}，预计耗时: ${approvalFlow.estimated_time || '-'}`}
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
        <Alert type="success" title="该环境类型无需审批，权限将直接回收" />
      )}

      <Form.Item
        name="reason"
        label="回收原因"
        style={{ marginTop: 16 }}
        rules={[{ required: true, message: '请填写回收原因' }]}
      >
        <Input.TextArea rows={3} placeholder="请说明回收原因" />
      </Form.Item>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <RollbackOutlined style={{ marginRight: 8 }} />
          回收协作权限
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
            { title: '选择回收对象' },
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
            description="回收后，目标组或成员将失去该应用指定环境类型的协作权限。"
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
              <Button type="primary" htmlType="submit" loading={loading} danger icon={<RollbackOutlined />}>
                提交回收申请
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

      {selectedApp && selectedEnvType && (
        <Card size="small" style={{ marginTop: 16 }} title="已选信息">
          <Descriptions column={3} size="small">
            <Descriptions.Item label="应用">
              <Space>
                <Text strong>{selectedApp.name}</Text>
                <Tag>{selectedApp.code}</Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="环境类型">
              <Tag color={ENV_TYPE_MAP[selectedEnvType]?.color || 'default'}>
                {ENV_TYPE_MAP[selectedEnvType]?.label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="回收对象">
              {recipientType === 'group' ? '指定组' : '指定成员'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  );
}