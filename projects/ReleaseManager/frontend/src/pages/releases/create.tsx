import { useEffect, useState } from 'react';
import {
  Form, Input, Select, Button, Typography, Space, InputNumber, message, Alert,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { appApi, releaseApi } from '../../api';

const { Title, Text } = Typography;
const { TextArea } = Input;

// 部署策略选项：主标题 + 简短说明（利用宽选择框双行展示）
const DEPLOY_STRATEGY_OPTIONS = [
  {
    value: 'rolling',
    label: (
      <div>
        <div>滚动更新 <Text type="secondary">(Rolling)</Text></div>
        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.6 }}>
          逐个替换 Pod，主入口版本更新为新版本，服务不中断
        </Text>
      </div>
    ),
  },
  {
    value: 'blue_green',
    label: (
      <div>
        <div>蓝绿部署 <Text type="secondary">(Blue/Green)</Text></div>
        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.6 }}>
          新建 blue 环境 + 切换 Service selector 切流，旧环境保留回滚
        </Text>
      </div>
    ),
  },
  {
    value: 'canary',
    label: (
      <div>
        <div>金丝雀发布 <Text type="secondary">(Canary)</Text></div>
        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.6 }}>
          新建 canary 独立入口，主入口旧版本 + 金丝雀新版本并存
        </Text>
      </div>
    ),
  },
];

// 部署策略 → 知识库文章锚点（backend/knowledge/docs/releases/articles/deploy-strategies.html）
const STRATEGY_DOC_ANCHOR: Record<string, string> = {
  rolling: 's2',      // 2. 滚动更新
  blue_green: 's3',   // 3. 蓝绿部署
  canary: 's4',       // 4. 灰度发布
};

// 策略详细说明：本 Demo 的隐藏配置约定 + 发布后自动验证点
const STRATEGY_INFO: Record<string, {
  title: string;
  intro: string;
  points: string[];
  verify: string[];
}> = {
  rolling: {
    title: '滚动更新 (Rolling)',
    intro: '逐个替换 Pod 完成发布，全程服务不中断，无需额外环境。',
    points: [
      '发布时自动同步容器 APP_VERSION 环境变量，保证 Pod 内版本号 = 发布版本',
      '旧 Pod 逐个下线、新 Pod 逐个上线，主入口（Service）始终可用',
    ],
    verify: ['部署就绪', '健康检查', '主入口版本 = 新版本'],
  },
  blue_green: {
    title: '蓝绿部署 (Blue/Green)',
    intro: '一套新环境 + 一个流量开关，发布 = 拨动开关。',
    points: [
      '隐藏约定：新环境命名 {app}-blue（如 python-app-blue），Pod 标签 track=blue',
      '旧环境 track=stable 保留不动，可随时一键回滚',
      '切换动作：把 Service selector 从 track=stable 改成 track=blue，一次开关瞬间切流',
      '注意：本 Demo 没有 green 环境 —— blue = 新环境，stable = 旧基线',
    ],
    verify: ['Service selector 切到 track=blue', '主入口版本 = 新版本'],
  },
  canary: {
    title: '金丝雀发布 (Canary)',
    intro: '先放一小部分流量验证新版本，确认无误后再全量发布。',
    points: [
      '隐藏约定：新建 {app}-canary 金丝雀环境 + 独立 Service 入口（如 python-app-canary）',
      '主入口保持旧版本不动，金丝雀独立入口运行新版本，按比例（canary_percent）放量',
      '人工确认金丝雀验证通过后，再全量发布到主环境',
    ],
    verify: ['主入口仍为旧版本', '金丝雀独立入口 = 新版本'],
  },
};

export default function CreateReleasePage() {
  const [form] = Form.useForm();
  const [searchParams] = useSearchParams();
  const [apps, setApps] = useState<any[]>([]);
  const [envConfigs, setEnvConfigs] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [commits, setCommits] = useState<any[]>([]);
  const [branchLoading, setBranchLoading] = useState(false);
  const [commitLoading, setCommitLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [strategy, setStrategy] = useState<string>('rolling');
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const navigate = useNavigate();

  // 从 URL 参数中获取预选应用 ID 和发布模式
  const preselectedAppId = searchParams.get('appId');
  const releaseMode = searchParams.get('mode') || 'regular';
  const cloneFromId = searchParams.get('cloneFrom');

  const fetchApps = () => {
    appApi.list().then((res: any) => {
      const appList = Array.isArray(res) ? res : (res?.data || []);
      setApps(appList);

      // 如果有预选应用，自动选中并加载环境配置
      if (preselectedAppId) {
        const appId = Number(preselectedAppId);
        setSelectedAppId(appId);
        form.setFieldsValue({ application: appId });
        handleAppChange(appId, cloneFromId ? Number(cloneFromId) : undefined);
      }
    });
  };

  useEffect(() => {
    fetchApps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAppChange = (appId: number, cloneFromId?: number) => {
    setSelectedAppId(appId);
    form.setFieldsValue({ env_config: undefined, branch: undefined, commit_id: undefined, commit_message: undefined });
    setEnvConfigs([]);
    setBranches([]);
    setCommits([]);

    if (!appId) return;

    // 加载环境配置
    appApi.envConfigs.list(appId).then((res: any) => {
      const cfgs = Array.isArray(res) ? res : (res?.data || []);
      setEnvConfigs(cfgs);

      // 克隆模式：加载源发布详情并预填
      if (cloneFromId) {
        releaseApi.detail(cloneFromId).then((relRes: any) => {
          const rel = relRes?.data || relRes;
          if (!rel) return;

          // 找到匹配的 env_config
          const envConfigId = rel.env_config || cfgs.find((c: any) =>
            c.environment_name === rel.environment_name || c.environment === rel.environment
          )?.id;

          form.setFieldsValue({
            title: `[克隆] ${rel.title || rel.release_no}`,
            version: rel.version || '',
            image_tag: rel.image_tag || '',
            description: rel.description || '',
            deploy_strategy: rel.deploy_strategy || 'rolling',
            canary_percent: rel.canary_percent,
            env_config: envConfigId,
          });
          if (rel.deploy_strategy) setStrategy(rel.deploy_strategy);
        }).catch(() => {});
      }
    });

    // 加载模拟分支
    setBranchLoading(true);
    appApi.branches.list(appId).then((res: any) => {
      const list = res?.data || [];
      setBranches(list);
      // 默认选中 main 分支并加载 commits
      const mainBranch = list.find((b: any) => b.is_default);
      if (mainBranch) {
        form.setFieldsValue({ branch: mainBranch.name });
        handleBranchChange(mainBranch.name);
      }
    }).finally(() => setBranchLoading(false));
  };

  const handleBranchChange = (branchName: string) => {
    form.setFieldsValue({ commit_id: undefined, commit_message: undefined });
    setCommits([]);
    if (!branchName || !selectedAppId) return;

    setCommitLoading(true);
    appApi.commits.list(selectedAppId, branchName).then((res: any) => {
      const list = res?.data || [];
      setCommits(list);
      // 自动选中第一个 commit
      if (list.length > 0) {
        form.setFieldsValue({
          commit_id: list[0].sha,
          commit_message: list[0].message,
        });
      }
    }).finally(() => setCommitLoading(false));
  };

  const handleCommitChange = (sha: string) => {
    const commit = commits.find((c) => c.sha === sha);
    if (commit) {
      form.setFieldsValue({ commit_message: commit.message });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const res = await releaseApi.create(values);
      message.success('发布创建成功');
      navigate(`/releases/${res.data?.id}`);
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error('创建发布失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          返回
        </Button>
        <Title level={4} style={{ margin: 0 }}>新建发布</Title>
      </div>

      <Form
        form={form}
        layout="vertical"
        style={{ maxWidth: 700 }}
        onFinish={handleSubmit}
        initialValues={{ deploy_strategy: 'rolling' }}
      >
        <Form.Item
          name="title"
          label="标题"
          rules={[{ required: true, message: '请输入发布标题' }]}
        >
          <Input placeholder="例如：v2.3.0 版本发布" />
        </Form.Item>

        <Form.Item
          name="application"
          label="应用"
          rules={[{ required: true, message: '请选择应用' }]}
        >
          <Select
            placeholder="请选择应用"
            showSearch
            optionFilterProp="label"
            disabled={!!preselectedAppId}
            onChange={handleAppChange}
            options={apps.map((app: any) => ({
              value: app.id,
              label: app.name,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="env_config"
          label="环境配置"
          rules={[{ required: true, message: '请选择环境配置' }]}
        >
          <Select
            placeholder="请先选择应用"
            showSearch
            optionFilterProp="label"
            disabled={envConfigs.length === 0}
            options={envConfigs.map((cfg: any) => ({
              value: cfg.id,
              label: `${cfg.environment_name || cfg.environment} - ${cfg.namespace_name || cfg.namespace || ''}`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="version"
          label="版本号"
          rules={[{ required: true, message: '请输入版本号' }]}
        >
          <Input placeholder="例如：v2.3.0" />
        </Form.Item>

        {/* Git 分支选择 */}
        <Form.Item
          name="branch"
          label="Git 分支"
          rules={[{ required: true, message: '请选择 Git 分支' }]}
        >
          <Select
            placeholder="请先选择应用"
            loading={branchLoading}
            disabled={branches.length === 0}
            onChange={handleBranchChange}
            options={branches.map((b: any) => ({
              value: b.name,
              label: `${b.name}${b.is_default ? ' (默认)' : ''}${b.protected ? ' 🔒' : ''}`,
            }))}
          />
        </Form.Item>

        {/* Commit 选择 */}
        <Form.Item
          name="commit_id"
          label="Git Commit"
          rules={[{ required: true, message: '请选择 Commit' }]}
        >
          <Select
            placeholder="请先选择分支"
            loading={commitLoading}
            disabled={commits.length === 0}
            showSearch
            optionFilterProp="label"
            onChange={handleCommitChange}
            options={commits.map((c: any) => ({
              value: c.sha,
              label: `${c.short_sha} - ${c.message}`,
            }))}
          />
        </Form.Item>

        {/* 选中 commit 后自动填充的提交信息 */}
        <Form.Item name="commit_message" label="提交信息">
          <TextArea rows={2} placeholder="选择 Commit 后自动填充" readOnly />
        </Form.Item>

        <Form.Item
          name="image_tag"
          label="镜像标签"
          rules={[{ required: true, message: '请输入镜像标签' }]}
        >
          <Input placeholder="例如：registry.example.com/app:v2.3.0" />
        </Form.Item>

        <Form.Item name="description" label="描述">
          <TextArea rows={3} placeholder="发布描述（可选）" />
        </Form.Item>

        <Form.Item
          name="deploy_strategy"
          label="部署策略"
          rules={[{ required: true, message: '请选择部署策略' }]}
        >
          <Select
            options={DEPLOY_STRATEGY_OPTIONS}
            onChange={(val) => setStrategy(val)}
          />
        </Form.Item>

        {/* 策略详细说明：本 Demo 的隐藏配置约定 + 发布后自动验证点 */}
        {strategy && STRATEGY_INFO[strategy] && (
          <div style={{ marginBottom: 24 }}>
            <Alert
              type="info"
              showIcon
              style={{ background: '#f0f5ff', borderColor: '#adc6ff' }}
              message={<Text strong>{STRATEGY_INFO[strategy].title}</Text>}
              description={
                <div>
                  <div style={{ fontSize: 13, marginBottom: 4 }}>
                    {STRATEGY_INFO[strategy].intro}
                  </div>
                  <ul style={{ margin: '4px 0', paddingLeft: 18 }}>
                    {STRATEGY_INFO[strategy].points.map((p: string, i: number) => (
                      <li key={i} style={{ fontSize: 13, lineHeight: 1.9 }}>{p}</li>
                    ))}
                  </ul>
                  <div style={{ fontSize: 13, marginTop: 6 }}>
                    <Text type="secondary">🔍 发布成功后自动验证：</Text>
                    <Text>{STRATEGY_INFO[strategy].verify.join('  ·  ')}</Text>
                  </div>
                  <Typography.Link
                    onClick={() => window.open(
                      `/knowledge/docs?module=releases&article=deploy-strategies&section=${STRATEGY_DOC_ANCHOR[strategy] || ''}`,
                      '_blank',
                    )}
                    style={{ fontSize: 13, display: 'inline-block', marginTop: 8 }}
                  >
                    📖 查看「{STRATEGY_INFO[strategy].title}」策略说明（本 Demo 实现 / 真实环境 / EC2）
                  </Typography.Link>
                </div>
              }
            />
          </div>
        )}

        {strategy === 'canary' && (
          <Form.Item
            name="canary_percent"
            label="金丝雀比例 (%)"
            rules={[{ required: true, message: '请输入金丝雀比例' }]}
          >
            <InputNumber
              min={1}
              max={100}
              style={{ width: 200 }}
              placeholder="例如：10"
            />
          </Form.Item>
        )}

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>
              提交
            </Button>
            <Button onClick={() => navigate('/releases')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
}