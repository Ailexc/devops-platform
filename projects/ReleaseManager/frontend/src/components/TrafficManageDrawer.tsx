import { useState, useEffect } from 'react';
import {
  Drawer, Select, Button, Typography, Space, Tag, Divider,
  message, Input, Empty, Descriptions, Radio,
} from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, CheckOutlined } from '@ant-design/icons';
import { appApi } from '../api';

const { Text } = Typography;

const DEPLOY_TYPE_LABELS: Record<string, string> = {
  k8s: 'Kubernetes',
  ec2: 'EC2 / 虚拟机',
};

interface TrafficManageDrawerProps {
  open: boolean;
  onClose: () => void;
  appId: number;
  appName: string;
  envConfigs: any[];
  onSuccess?: () => void;
}

export default function TrafficManageDrawer({ open, onClose, appId, appName, envConfigs, onSuccess }: TrafficManageDrawerProps) {
  const [selectedEnvCode, setSelectedEnvCode] = useState<string | undefined>(undefined);
  const [trafficAction, setTrafficAction] = useState<'take_out' | 'restore'>('take_out');
  const [reason, setReason] = useState('');
  const [executing, setExecuting] = useState(false);
  const [execMessage, setExecMessage] = useState('');

  const selectedConfig = envConfigs.find((c: any) => c.environment_code === selectedEnvCode);
  const deployType = selectedConfig?.environment_deploy_type || 'k8s';
  const isK8s = deployType === 'k8s';

  // Drawer 关闭时重置表单状态
  useEffect(() => {
    if (!open) {
      setSelectedEnvCode(undefined);
      setTrafficAction('take_out');
      setReason('');
      setExecMessage('');
    }
  }, [open]);

  const envOptions = envConfigs.map((cfg: any) => ({
    value: cfg.environment_code,
    label: (
      <Space>
        <span>{cfg.environment_name}</span>
        <Tag color={cfg.environment_deploy_type === 'ec2' ? 'orange' : 'blue'} style={{ marginLeft: 4 }}>
          {cfg.environment_deploy_type === 'ec2' ? 'EC2' : 'K8s'}
        </Tag>
      </Space>
    ),
  }));

  const handleSubmit = async () => {
    if (!selectedConfig) return;
    setExecuting(true);
    setExecMessage('');
    try {
      const res: any = await appApi.operations(appId, {
        env_code: selectedConfig.environment_code,
        action: 'traffic',
        traffic_action: trafficAction,
        reason: reason || undefined,
      });
      const data = res?.data || res;
      if (data.requires_approval) {
        message.info(data.message || '操作已提交审批');
      } else {
        message.success(data.message || '流量管理发布单已创建');
      }
      onClose();
      onSuccess?.();
    } catch (e: any) {
      const errMsg = e?.response?.data?.message || e?.message || '操作失败';
      message.error(errMsg);
      setExecMessage(`❌ ${errMsg}`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <Drawer
      title={
        <Space>
          <span>流量管理</span>
          <Text type="secondary" style={{ fontSize: 13, fontWeight: 'normal' }}>{appName}</Text>
        </Space>
      }
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
    >
      {/* 环境选择 */}
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>选择环境</Text>
        <Select
          placeholder="选择要操作的环境"
          style={{ width: '100%' }}
          value={selectedEnvCode}
          onChange={setSelectedEnvCode}
          options={envOptions}
          allowClear
        />
      </div>

      {selectedConfig && (
        <>
          <Descriptions column={1} size="small" bordered style={{ marginBottom: 20 }}>
            <Descriptions.Item label="环境">{selectedConfig.environment_name}</Descriptions.Item>
            <Descriptions.Item label="部署类型">
              <Tag color={isK8s ? 'blue' : 'orange'}>
                {DEPLOY_TYPE_LABELS[deployType] || deployType}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          <Divider style={{ margin: '16px 0' }} />

          {/* 动作选择 */}
          <div style={{ marginBottom: 16 }}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>选择操作</Text>
            <Radio.Group
              value={trafficAction}
              onChange={(e) => { setTrafficAction(e.target.value); setExecMessage(''); }}
              style={{ width: '100%' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size={8}>
                <Radio.Button
                  value="take_out"
                  style={{ width: '100%', height: 'auto', padding: '10px 12px', display: 'block', whiteSpace: 'normal' }}
                >
                  <Space>
                    <ArrowDownOutlined />
                    <span>摘流（下线）</span>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      将服务从流量中摘除，实例保留但不再接收请求
                    </Text>
                  </Space>
                </Radio.Button>
                <Radio.Button
                  value="restore"
                  style={{ width: '100%', height: 'auto', padding: '10px 12px', display: 'block', whiteSpace: 'normal' }}
                >
                  <Space>
                    <ArrowUpOutlined />
                    <span>挂流（上线）</span>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      将服务重新挂回流量，恢复接收请求
                    </Text>
                  </Space>
                </Radio.Button>
              </Space>
            </Radio.Group>
          </div>

          {/* 实现说明 */}
          <div style={{ marginBottom: 20, lineHeight: 2 }}>
            <Text strong>📝 实现方式：</Text>
            <ul style={{ paddingLeft: 20, marginTop: 8 }}>
              {isK8s ? (
                <li>K8s 场景：修改 Service Selector 标签控制 Pod 是否接收流量</li>
              ) : (
                <>
                  <li>EC2 场景：通过 AWS ALB Target Group 的 deregister/register 操作控制实例流量</li>
                  <li>EKS 场景：通过修改 Service Selector 标签控制 Pod 是否接收流量</li>
                </>
              )}
            </ul>
          </div>

          {/* 操作原因 */}
          <div style={{ marginBottom: 20 }}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>操作原因</Text>
            <Input
              placeholder="可选，填写操作原因"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={executing}
            />
          </div>

          {/* 确认按钮 */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={handleSubmit}
              loading={executing}
            >
              确认
            </Button>
          </div>

          {/* 执行结果 */}
          {execMessage && (
            <div style={{
              padding: '8px 12px',
              borderRadius: 4,
              background: execMessage.startsWith('✅') ? '#f6ffed'
                : execMessage.startsWith('❌') ? '#fff2f0' : '#e6f7ff',
              fontSize: 13,
            }}>
              {execMessage}
            </div>
          )}
        </>
      )}

      {!selectedConfig && (
        <Empty description="请选择环境" style={{ marginTop: 60 }} />
      )}
    </Drawer>
  );
}
