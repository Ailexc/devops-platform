import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card, Form, Select, Button, Input, Switch, message, Typography,
  Space, Steps, Alert, Divider, DatePicker,
} from 'antd';
import { ArrowLeftOutlined, PlusOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/useAuthStore';
import { orgApi, appApi, infraApi, authzApi } from '../../api';

const { Title } = Typography;

const ENV_TYPES = [
  { value: 'dev', label: '开发' },
  { value: 'test', label: '测试' },
  { value: 'staging', label: '预发' },
  { value: 'prod', label: '生产' },
];

export default function PermissionApplyPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [approvalFlow, setApprovalFlow] = useState<any>(null);

  const [businessLines, setBusinessLines] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [apps, setApps] = useState<any[]>([]);
  const [envs, setEnvs] = useState<any[]>([]);
  const [leaderInfo, setLeaderInfo] = useState<any>(null);
  const [myPermissions, setMyPermissions] = useState<any>(null);

  const businessLineId = Form.useWatch('business_line_id', form);
  const envType = Form.useWatch('env_type', form);
  const isAllEnvs = Form.useWatch('is_all_envs', form);
  const isCrossGroup = Form.useWatch('grant_scope', form) === 'cross_group';

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [blRes, groupRes, envRes, leaderRes, permRes] = await Promise.all([
        orgApi.businessLines.list(),
        orgApi.groups.list(),
        infraApi.environments.list(),
        authzApi.businessLineLeader(),
        authzApi.myPermissions(),
      ]);
      setBusinessLines(blRes?.data || []);
      setGroups(groupRes?.data || []);
      setEnvs(Array.isArray(envRes) ? envRes : (envRes?.data || []));
      setLeaderInfo(leaderRes?.data);
      setMyPermissions(permRes?.data);
    } catch {
      message.error('加载基础数据失败');
    }
  };

  useEffect(() => {
    if (!businessLineId) return;
    appApi.list({ business_line_id: businessLineId }).then((res: any) => {
      setApps(res?.data || []);
    }).catch(() => setApps([]));
  }, [businessLineId]);

  useEffect(() => {
    if (!myPermissions || !groups.length || !businessLines.length) return;

    const primaryGroup = myPermissions.groups?.find((g: any) => g.membership_type === 'primary');
    if (primaryGroup) {
      const group = groups.find((g) => g.id === primaryGroup.group_id);
      if (group) {
        form.setFieldsValue({
          business_line_id: group.business_line || group.business_line_id,
          group_id: group.id,
        });
      }
    } else if (leaderInfo?.business_line?.id) {
      form.setFieldsValue({ business_line_id: leaderInfo.business_line.id });
    }
  }, [myPermissions, groups, businessLines, leaderInfo, form]);

  const availableGroups = useMemo(() => {
    if (!businessLineId) return [];
    return groups.filter((g) => g.business_line === businessLineId || g.business_line_id === businessLineId);
  }, [groups, businessLineId]);

  const envOptions = useMemo(() => {
    if (!envType) return [];
    return envs.filter((e) => e.env_type === envType).map((e) => ({ label: e.name, value: e.id }));
  }, [envs, envType]);

  const handleBusinessLineChange = () => {
    form.setFieldsValue({ group_id: undefined, app_id: undefined });
  };

  const handleEnvTypeChange = () => {
    form.setFieldsValue({ env_ids: [] });
    setApprovalFlow(null);
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
        grant_scope: values.grant_scope || 'own_group',
      });
      setApprovalFlow(res.data);
      setCurrentStep(2);
    } catch {
      message.error('计算审批流失败');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    setLoading(true);
    try {
      const payload: any = {
        request_type: 'apply',
        app_id: values.app_id,
        env_type: values.env_type,
        is_all_envs: values.is_all_envs || false,
        env_ids: values.is_all_envs ? [] : (values.env_ids || []),
        grant_scope: values.grant_scope || 'own_group',
        reason: values.reason,
        extra_data: {
          target_group_id: values.group_id,
        },
      };
      if (isCrossGroup && values.valid_range) {
        payload.valid_from = values.valid_range[0].toISOString();
        payload.valid_to = values.valid_range[1].toISOString();
      }
      await authzApi.permissionRequests.create(payload);
      message.success('权限申请已提交');
      navigate('/permissions/apply-records');
    } catch {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <PlusOutlined style={{ marginRight: 8 }} />
          申请权限
        </Title>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/permissions/apply-records')}>
          返回申请记录
        </Button>
      </div>

      <Card size="small">
        <Steps
          current={currentStep}
          size="small"
          style={{ marginBottom: 24 }}
          items={[
            { title: '选择业务线/组/应用' },
            { title: '选择环境' },
            { title: '预览审批流' },
            { title: '提交申请' },
          ]}
        />

        {leaderInfo?.leader && (
          <Alert
            type="info"
            showIcon
            title={`当前业务线负责人: ${leaderInfo.leader.name}`}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <div style={{ display: currentStep >= 0 ? 'block' : 'none' }}>
            <Form.Item
              name="business_line_id"
              label="业务线"
              rules={[{ required: true, message: '请选择业务线' }]}
            >
              <Select
                showSearch
                placeholder="选择业务线"
                optionFilterProp="label"
                options={businessLines.map((bl) => ({ value: bl.id, label: bl.name }))}
                onChange={handleBusinessLineChange}
              />
            </Form.Item>

            <Form.Item
              name="group_id"
              label="申请组"
              rules={[{ required: true, message: '请选择组' }]}
            >
              <Select
                showSearch
                placeholder="选择申请权限的组"
                optionFilterProp="label"
                disabled={!businessLineId}
                options={availableGroups.map((g) => ({
                  value: g.id,
                  label: `${g.name}${g.business_line_name ? ` (${g.business_line_name})` : ''}`,
                }))}
                onChange={() => form.setFieldsValue({ app_id: undefined })}
              />
            </Form.Item>

            <Form.Item
              name="app_id"
              label="选择应用"
              rules={[{ required: true, message: '请选择应用' }]}
            >
              <Select
                showSearch
                placeholder="搜索应用"
                optionFilterProp="label"
                options={apps.map((a) => ({ value: a.id, label: `${a.name} (${a.code})` }))}
              />
            </Form.Item>
          </div>

          <div style={{ display: currentStep >= 1 ? 'block' : 'none' }}>
            <Form.Item
              name="env_type"
              label="环境类型"
              rules={[{ required: true, message: '请选择环境类型' }]}
            >
              <Select options={ENV_TYPES} placeholder="选择环境类型" onChange={handleEnvTypeChange} />
            </Form.Item>

            <Form.Item name="is_all_envs" label="全部环境" valuePropName="checked" initialValue={false}>
              <Switch />
            </Form.Item>

            {!isAllEnvs && (
              <Form.Item
                name="env_ids"
                label="具体环境"
                rules={[{ required: true, message: '请选择具体环境' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="选择环境实例"
                  allowClear
                  options={envOptions}
                />
              </Form.Item>
            )}

            <Form.Item
              name="grant_scope"
              label="授权范围"
              initialValue="own_group"
              rules={[{ required: true }]}
            >
              <Select
                onChange={() => setApprovalFlow(null)}
                options={[
                  { value: 'own_group', label: '本组权限' },
                  { value: 'cross_group', label: '跨组协作' },
                ]}
              />
            </Form.Item>

            {isCrossGroup && (
              <Form.Item
                name="valid_range"
                label="有效期（跨组协作必填）"
                rules={[{ required: true, message: '跨组协作需设置有效期' }]}
              >
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
            )}
          </div>

          {currentStep >= 2 && approvalFlow && (
            <div style={{ marginBottom: 16 }}>
              <Divider>审批流预览</Divider>
              {approvalFlow.requires_approval ? (
                <Alert
                  type="warning"
                  title={`审批流模板: ${approvalFlow.flow_template_name}，预计耗时: ${approvalFlow.estimated_time || '-'}`}
                  style={{ marginBottom: 12 }}
                />
              ) : (
                <Alert type="success" title="该环境类型无需审批，权限将直接生效" />
              )}

              <Steps
                direction="vertical"
                size="small"
                current={-1}
                items={(approvalFlow.steps || []).map((step: any) => ({
                  title: step.name,
                  description: (
                    <div>
                      <div>审批人: {step.approvers?.map((a: any) => a.name).join(', ') || '待定'}</div>
                      <div style={{ color: '#888' }}>
                        需 {step.required_count || 1} 人审批 · 超时 {step.timeout_hours || 24}h
                      </div>
                    </div>
                  ),
                }))}
              />

              <Form.Item name="reason" label="申请原因" style={{ marginTop: 16 }}>
                <Input.TextArea rows={3} placeholder="请说明申请原因" />
              </Form.Item>
            </div>
          )}

          <Space>
            {currentStep === 0 && (
              <Button type="primary" onClick={() => setCurrentStep(1)}>
                下一步：选择环境
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
              <Button onClick={() => setCurrentStep(currentStep - 1)}>上一步</Button>
            )}
            <Button onClick={() => { form.resetFields(); setCurrentStep(0); setApprovalFlow(null); }}>
              重置
            </Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
