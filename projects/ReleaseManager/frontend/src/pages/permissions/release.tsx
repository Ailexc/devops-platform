import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card, Form, Select, Button, Input, Radio, Checkbox, message, Typography,
  Space, Steps, Alert, Divider, Tag, Descriptions,
} from 'antd';
import { ArrowLeftOutlined, DisconnectOutlined } from '@ant-design/icons';
import { appApi, infraApi, authzApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPE_MAP: Record<string, { label: string; color: string }> = {
  dev: { label: '开发', color: 'green' },
  test: { label: '测试', color: 'blue' },
  staging: { label: '预发', color: 'orange' },
  prod: { label: '生产', color: 'red' },
};

export default function ReleaseCollaborationPage() {
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

  const selectedAppId = Form.useWatch('app_id', form);
  const selectedEnvType = Form.useWatch('env_type', form);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [appRes, envRes] = await Promise.all([
        appApi.list(),
        infraApi.environments.list(),
      ]);
      setApps(Array.isArray(appRes) ? appRes : (appRes?.data || []));
      setEnvs(Array.isArray(envRes) ? envRes : (envRes?.data || []));
    } catch {
      message.error('加载基础数据失败');
    }
  };

  const envOptions = useMemo(() => {
    if (!selectedEnvType) return [];
    return envs
      .filter((e) => e.env_type === selectedEnvType)
      .map((e) => ({ label: e.name, value: e.id }));
  }, [envs, selectedEnvType]);

  const selectedApp = useMemo(() => apps.find((a) => a.id === selectedAppId), [apps, selectedAppId]);

  const handleEnvTypeChange = () => {
    form.setFieldsValue({ env_ids: [] });
    setApprovalFlow(null);
    if (currentStep >= 1) setCurrentStep(0);
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
      setCurrentStep(1);
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
        request_type: 'release',
        app_id: values.app_id,
        env_type: values.env_type,
        is_all_envs: values.is_all_envs || false,
        env_ids: values.is_all_envs ? [] : (values.env_ids || []),
        grant_scope: 'cross_group',
        reason: values.reason,
        extra_data: {
          owner_group_id: values.owner_group_id || 0,
        },
      };

      await authzApi.permissionRequests.create(payload);
      message.success('解除协作应用申请已提交');
      navigate('/permissions');
    } catch {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  const appEnvSection = (
    <div>
      <Divider>应用与环境</Divider>
      <Form.Item
        name="app_id"
        label="选择应用"
        rules={[{ required: true, message: '请选择应用' }]}
        initialValue={appId || undefined}
      >
        <Select
          showSearch
          placeholder="搜索要解除协作的应用"
          optionFilterProp="label"
          options={apps.map((a) => ({
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
        <Alert type="success" title="该环境类型无需审批，协作将直接解除" />
      )}

      <Form.Item
        name="reason"
        label="解除原因"
        style={{ marginTop: 16 }}
        rules={[{ required: true, message: '请填写解除原因' }]}
      >
        <Input.TextArea rows={3} placeholder="请说明解除协作应用的原因" />
      </Form.Item>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <DisconnectOutlined style={{ marginRight: 8 }} />
          解除协作应用
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
            { title: '选择应用环境' },
            { title: '预览审批流' },
            { title: '提交申请' },
          ]}
        />

        <Alert
          type="info"
          showIcon
          title="解除协作应用"
          description="解除后，当前组将失去该应用指定环境类型的协作权限。此操作需经审批。"
          style={{ marginBottom: 16 }}
        />

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <div style={{ display: currentStep >= 0 ? 'block' : 'none' }}>
            {appEnvSection}
          </div>

          <div style={{ display: currentStep >= 1 ? 'block' : 'none' }}>
            {approvalPreviewSection}
          </div>

          <Space style={{ marginTop: 16 }}>
            {currentStep === 0 && (
              <Button type="primary" onClick={handlePreviewApproval} loading={previewLoading}>
                预览审批流
              </Button>
            )}
            {currentStep === 1 && (
              <Button type="primary" htmlType="submit" loading={loading} danger icon={<DisconnectOutlined />}>
                提交解除申请
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
          <Descriptions column={2} size="small">
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
          </Descriptions>
        </Card>
      )}
    </div>
  );
}