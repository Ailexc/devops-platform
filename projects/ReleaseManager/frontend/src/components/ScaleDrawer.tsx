import { useState, useEffect } from 'react';
import {
  Drawer, Select, Button, InputNumber, Typography, Space, Tag, Divider,
  message, Input, Empty, Descriptions,
} from 'antd';
import { MinusOutlined, PlusOutlined, CheckOutlined } from '@ant-design/icons';
import { appApi } from '../api';

const { Text, Title } = Typography;

const DEPLOY_TYPE_LABELS: Record<string, string> = {
  k8s: 'Kubernetes',
  ec2: 'EC2 / 虚拟机',
};

interface ScaleDrawerProps {
  open: boolean;
  onClose: () => void;
  appId: number;
  appName: string;
  envConfigs: any[];
  onSuccess?: () => void;
}

export default function ScaleDrawer({ open, onClose, appId, appName, envConfigs, onSuccess }: ScaleDrawerProps) {
  const [selectedEnvCode, setSelectedEnvCode] = useState<string | undefined>(undefined);
  const [targetReplicas, setTargetReplicas] = useState<number>(0);
  const [reason, setReason] = useState('');
  const [executing, setExecuting] = useState(false);
  const [execMessage, setExecMessage] = useState('');

  const selectedConfig = envConfigs.find((c: any) => c.environment_code === selectedEnvCode);
  const maxReplicas = selectedConfig?.replicas ?? 0;
  const deployType = selectedConfig?.environment_deploy_type || 'k8s';
  const isK8s = deployType === 'k8s';

  // 切换环境时重置目标副本数为当前值
  useEffect(() => {
    if (selectedConfig) {
      setTargetReplicas(selectedConfig.replicas);
      setExecMessage('');
    }
  }, [selectedEnvCode]);

  // Drawer 关闭时重置表单状态
  useEffect(() => {
    if (!open) {
      setSelectedEnvCode(undefined);
      setTargetReplicas(0);
      setReason('');
      setExecMessage('');
    }
  }, [open]);

  const handleScale = async () => {
    if (!selectedConfig) return;
    if (targetReplicas === selectedConfig.replicas) {
      message.warning('目标实例数与当前相同，无需操作');
      return;
    }
    setExecuting(true);
    setExecMessage('');
    try {
      const res: any = await appApi.scale(appId, {
        env_code: selectedConfig.environment_code,
        target_replicas: targetReplicas,
        reason: reason || `手动伸缩: ${selectedConfig.replicas} → ${targetReplicas}`,
      });
      const data = res?.data || res;
      if (data.requires_approval) {
        message.info(data.message || '操作已提交审批');
        onClose();
        onSuccess?.();
      } else {
        message.success(data.message || '伸缩操作已提交');
        onClose();
        onSuccess?.();
      }
    } catch (e: any) {
      const errMsg = e?.response?.data?.message || e?.message || '操作失败';
      message.error(errMsg);
      setExecMessage(`❌ ${errMsg}`);
    } finally {
      setExecuting(false);
    }
  };

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

  return (
    <Drawer
      title={
        <Space>
          <span>实例伸缩</span>
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
          placeholder="选择要伸缩的环境"
          style={{ width: '100%' }}
          value={selectedEnvCode}
          onChange={setSelectedEnvCode}
          options={envOptions}
          allowClear
        />
      </div>

      {/* 选中环境后的信息卡片 */}
      {selectedConfig && (
        <>
          <Descriptions
            column={1}
            size="small"
            bordered
            style={{ marginBottom: 20 }}
          >
            <Descriptions.Item label="环境">{selectedConfig.environment_name}</Descriptions.Item>
            <Descriptions.Item label="部署类型">
              <Tag color={isK8s ? 'blue' : 'orange'}>
                {DEPLOY_TYPE_LABELS[deployType] || deployType}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="部署策略">
              {selectedConfig.deploy_strategy === 'rolling' ? '滚动更新'
                : selectedConfig.deploy_strategy === 'blue_green' ? '蓝绿部署' : '灰度'}
            </Descriptions.Item>
            <Descriptions.Item label="当前实例">
              <Text strong>
                {isK8s
                  ? `${selectedConfig.replicas}/${selectedConfig.replicas} Pods Running`
                  : `${selectedConfig.replicas} 台机器运行中`}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="配置上限">
              {selectedConfig.replicas}
              <Text type="secondary" style={{ marginLeft: 4, fontSize: 12 }}>
                （应用管理 → 环境配置）
              </Text>
            </Descriptions.Item>
          </Descriptions>

          <Divider style={{ margin: '16px 0' }} />

          {/* 目标实例数 */}
          <div style={{ marginBottom: 16 }}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>目标实例数</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
              <Button
                icon={<MinusOutlined />}
                onClick={() => setTargetReplicas(Math.max(0, targetReplicas - 1))}
                disabled={targetReplicas <= 0 || executing}
              />
              <InputNumber
                min={0}
                max={maxReplicas}
                value={targetReplicas}
                onChange={(v) => setTargetReplicas(v ?? 0)}
                disabled={executing}
                style={{ width: 80, textAlign: 'center' }}
                size="large"
              />
              <Button
                icon={<PlusOutlined />}
                onClick={() => setTargetReplicas(Math.min(maxReplicas, targetReplicas + 1))}
                disabled={targetReplicas >= maxReplicas || executing}
              />
            </div>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', textAlign: 'center', marginTop: 8 }}>
              (0~{maxReplicas} 范围，不能超过配置上限)
            </Text>
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

          {/* 确认按钮（右下角） */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              onClick={handleScale}
              loading={executing}
              disabled={targetReplicas === selectedConfig.replicas}
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
