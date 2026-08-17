import { useEffect, useMemo, useState } from 'react';
import { Card, Descriptions, Table, Tag, Typography, Space, Tabs } from 'antd';
import { useAuthStore } from '../../store/useAuthStore';
import { authzApi, infraApi, appApi } from '../../api';

const { Title, Text } = Typography;

const ENV_TYPE_TAG_COLORS: Record<string, string> = {
  dev: 'green',
  test: 'blue',
  staging: 'orange',
  prod: 'red',
};

const PERMISSION_SOURCE_COLORS: Record<string, string> = {
  group: 'blue',
  personal: 'purple',
  mixed: 'magenta',
  cross: 'orange',
  team: 'blue',
};

const APP_TYPE_MAP: Record<string, string> = {
  web: 'Web 应用',
  backend: '后端服务',
  mobile: '移动应用',
  middleware: '中间件',
  job: '定时任务',
  data: '数据服务',
};

const LANGUAGE_MAP: Record<string, string> = {
  python: 'Python',
  go: 'Go',
  node: 'Node.js',
  java: 'Java',
  other: '其他',
};

interface EnvInfo {
  id: number;
  name: string;
  code: string;
  env_type: string;
  cloud_provider?: string;
  cloud_provider_label?: string;
  account_id?: string;
  region?: string;
  zone?: string;
  network_type?: string;
}

interface EnvPermission {
  env_type: string;
  env_type_label: string;
  scope: 'all' | 'partial' | 'none';
  allowed_envs: EnvInfo[];
  unauthorized_envs: EnvInfo[];
  denied_envs: EnvInfo[];
  permission_source: 'group' | 'personal' | 'mixed' | 'cross' | 'team';
  permission_source_label: string;
}

interface AppPermission {
  app_id: number;
  app_name: string;
  app_code: string;
  business_line_name: string;
  owner_group_name: string;
  env_permissions: EnvPermission[];
}

interface EnvDetail extends EnvInfo {
  status: 'allowed' | 'denied' | 'unauthorized';
  permission_source?: 'team' | 'personal' | 'mixed';
}

const envTypeOrder = (envType: string) => {
  const order = ['dev', 'test', 'staging', 'prod'];
  return order.indexOf(envType) === -1 ? 99 : order.indexOf(envType);
};

export default function MyPermissionsPage() {
  const { user } = useAuthStore();
  const [permissions, setPermissions] = useState<any>(null);
  const [apps, setApps] = useState<any[]>([]);
  const [envs, setEnvs] = useState<EnvInfo[]>([]);

  useEffect(() => {
    if (user) {
      authzApi.myPermissions().then((res: any) => {
        setPermissions(res.data);
      });
    }
    loadApps();
    loadEnvs();
  }, [user]);

  const loadApps = async () => {
    try {
      const res = await appApi.list();
      setApps(Array.isArray(res) ? res : (res.data || []));
    } catch {
      // ignore
    }
  };

  const loadEnvs = async () => {
    try {
      const res = await infraApi.environments.list();
      setEnvs(Array.isArray(res) ? res : (res.data || []));
    } catch {
      // ignore
    }
  };

  const renderEnvStatusTag = (status: EnvDetail['status']) => {
    if (status === 'allowed') return <Tag color="green">已授权</Tag>;
    if (status === 'denied') return <Tag color="red">已拒绝</Tag>;
    return <Tag>未授权</Tag>;
  };

  const buildEnvDetails = (envPerm: EnvPermission): EnvDetail[] => {
    return [
      ...envPerm.allowed_envs.map((e) => ({ ...e, status: 'allowed' as const, permission_source: envPerm.permission_source === 'personal' ? 'personal' : envPerm.permission_source === 'mixed' ? 'mixed' : 'team' as const })),
      ...envPerm.denied_envs.map((e) => ({ ...e, status: 'denied' as const })),
      ...envPerm.unauthorized_envs.map((e) => ({ ...e, status: 'unauthorized' as const })),
    ];
  };

  const renderEnvDetailTable = (appId: number, envPerm: EnvPermission) => {
    const dataSource = buildEnvDetails(envPerm);
    if (dataSource.length === 0) {
      return <Text type="secondary">暂无环境详情</Text>;
    }
    const cloudProviderLabels: Record<string, string> = {
      aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', huawei: '华为云', azure: 'Azure', gcp: 'GCP',
    };
    return (
      <Table
        dataSource={dataSource}
        columns={[
          { title: '环境名称', dataIndex: 'name', key: 'name', width: 140 },
          { title: '环境编码', dataIndex: 'code', key: 'code', width: 120, render: (v: string) => <Tag color="default" style={{ fontSize: '10px' }}>{v}</Tag> },
          {
            title: '云厂商',
            key: 'cloud_provider',
            width: 100,
            render: (_: any, record: any) => cloudProviderLabels[record.cloud_provider] || record.cloud_provider || '-',
          },
          { title: '所属账号', dataIndex: 'account_id', key: 'account_id', width: 140, render: (v: string) => v || '-' },
          { title: '所属区域', dataIndex: 'region', key: 'region', width: 120, render: (v: string) => v || '-' },
          { title: '可用区', dataIndex: 'zone', key: 'zone', width: 90, render: (v: string) => v || '-' },
          {
            title: '权限状态',
            key: 'status',
            width: 110,
            render: (_: any, record: EnvDetail) => renderEnvStatusTag(record.status),
          },
          {
            title: '权限来源',
            key: 'source',
            width: 120,
            render: (_: any, record: EnvDetail) => {
              if (record.status !== 'allowed') return <Text type="secondary">-</Text>;
              const source = record.permission_source || 'team';
              const label = source === 'personal' ? '个人申请' : source === 'mixed' ? '混合' : '团队继承';
              return <Tag color={PERMISSION_SOURCE_COLORS[source] || 'default'} style={{ fontSize: '10px' }}>{label}</Tag>;
            },
          },
        ]}
        rowKey="id"
        size="small"
        pagination={false}
      />
    );
  };

  const renderEnvTypeTable = (appId: number, app: AppPermission) => {
    const dataSource = (app.env_permissions || []).sort(
      (a, b) => envTypeOrder(a.env_type) - envTypeOrder(b.env_type)
    );
    if (dataSource.length === 0) {
      return <Text type="secondary">暂无环境权限</Text>;
    }
    return (
      <div style={{ padding: '8px 16px', background: '#fafafa', borderRadius: 8 }}>
        <div style={{ fontWeight: 500, marginBottom: 12 }}>环境权限详情</div>
        <Table
          dataSource={dataSource}
          columns={[
            {
              title: '环境类型',
              dataIndex: 'env_type_label',
              key: 'env_type',
              width: 120,
              render: (v: string, record: EnvPermission) => (
                <Tag color={ENV_TYPE_TAG_COLORS[record.env_type] || 'default'}>{v}</Tag>
              ),
            },
            {
              title: '授权范围',
              key: 'scope',
              width: 110,
              render: (_: any, record: EnvPermission) => {
                if (record.scope === 'all') return <Tag color="green">全部环境</Tag>;
                if (record.scope === 'partial') return <Tag color="blue">部分环境</Tag>;
                return <Tag>未授权</Tag>;
              },
            },
            {
              title: '环境数量',
              key: 'env_count',
              width: 100,
              render: (_: any, record: EnvPermission) => `${record.allowed_envs.length + record.unauthorized_envs.length + record.denied_envs.length} 个`,
            },
            {
              title: '授权比例',
              key: 'auth_ratio',
              width: 100,
              render: (_: any, record: EnvPermission) => {
                const total = record.allowed_envs.length + record.unauthorized_envs.length + record.denied_envs.length;
                return `${record.allowed_envs.length}/${total}`;
              },
            },
            {
              title: '权限属性',
              key: 'permission_source',
              width: 140,
              render: (_: any, record: EnvPermission) => (
                <Tag color={PERMISSION_SOURCE_COLORS[record.permission_source] || 'default'}>
                  {record.permission_source_label}
                </Tag>
              ),
            },
          ]}
          expandable={{
            expandedRowRender: (record: EnvPermission) => renderEnvDetailTable(appId, record),
            rowExpandable: () => true,
          }}
          rowKey="env_type"
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  const appMap = useMemo(() => {
    const map = new Map<number, any>();
    apps.forEach((a) => map.set(a.id, a));
    return map;
  }, [apps]);

  const renderAppPermissionsTable = (appList: AppPermission[]) => {
    if (!appList || appList.length === 0) return <Text type="secondary">暂无权限</Text>;

    const dataSource = appList.map((app) => {
      const appInfo = appMap.get(app.app_id) || {};
      const total = app.env_permissions.reduce(
        (sum, ep) => sum + ep.allowed_envs.length + ep.unauthorized_envs.length + ep.denied_envs.length,
        0
      );
      const allowed = app.env_permissions.reduce((sum, ep) => sum + ep.allowed_envs.length, 0);
      return { ...app, appInfo, authorized_count: `${allowed}/${total}` };
    });

    const securityLevelMap: Record<string, { text: string; color: string }> = {
      public: { text: '公开', color: 'green' },
      internal: { text: '内部', color: 'blue' },
      confidential: { text: '机密', color: 'orange' },
      secret: { text: '绝密', color: 'red' },
    };

    return (
      <Table
        dataSource={dataSource}
        columns={[
          {
            title: '应用名称',
            dataIndex: 'app_name',
            key: 'app_name',
            width: 220,
            render: (_: any, record: any) => (
              <Space orientation="vertical" size={0}>
                <span style={{ fontWeight: 500 }}>{record.app_name}</span>
                <Tag color="default" style={{ fontSize: '10px' }}>{record.app_code}</Tag>
              </Space>
            ),
          },
          {
            title: '应用类型',
            key: 'app_type',
            width: 160,
            render: (_: any, record: any) => (
              <Space>
                <Tag color="blue">{APP_TYPE_MAP[record.appInfo.app_type] || record.appInfo.app_type || '-'}</Tag>
                <Tag color="default" style={{ fontSize: '10px' }}>{LANGUAGE_MAP[record.appInfo.language] || record.appInfo.language || '-'}</Tag>
              </Space>
            ),
          },
          {
            title: '业务线',
            key: 'business_line',
            width: 120,
            render: (_: any, record: any) => record.appInfo.business_line_name || record.business_line_name || '-',
          },
          {
            title: '承接组',
            key: 'owner_group',
            width: 140,
            render: (_: any, record: any) => record.appInfo.owner_group_name || record.owner_group_name || '-',
          },
          {
            title: '安全等级',
            key: 'security_level',
            width: 90,
            render: (_: any, record: any) => {
              const sl = securityLevelMap[record.appInfo.security_level] || { text: record.appInfo.security_level || '-', color: 'default' };
              return <Tag color={sl.color}>{sl.text}</Tag>;
            },
          },
          {
            title: '核心标识',
            key: 'is_core',
            width: 90,
            render: (_: any, record: any) => (
              <Tag color={record.appInfo.is_core ? 'red' : 'default'}>
                {record.appInfo.priority || '-'}
              </Tag>
            ),
          },
          {
            title: '已授权',
            key: 'authorized_count',
            width: 100,
            render: (_: any, record: any) => <Tag color="default">{record.authorized_count}</Tag>,
          },
        ]}
        expandable={{
          expandedRowRender: (record: any) => renderEnvTypeTable(record.app_id, record),
          rowExpandable: () => true,
        }}
        rowKey="app_id"
        size="small"
        pagination={false}
      />
    );
  };

  const ownGroupApps: AppPermission[] = permissions?.own_group_apps || [];
  const crossGroupApps: AppPermission[] = permissions?.cross_group_apps || [];

  return (
    <div>
      <Title level={4}>我的权限</Title>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={3}>
          <Descriptions.Item label="用户名">{user?.display_name}</Descriptions.Item>
          <Descriptions.Item label="归属组">
            {permissions?.groups
              ?.filter((g: any) => g.membership_type === 'primary')
              .map((g: any) => g.group_name)
              .join(', ') || '无'}
          </Descriptions.Item>
          <Descriptions.Item label="协作组">
            {permissions?.groups
              ?.filter((g: any) => g.membership_type === 'collaborator')
              .map((g: any) => g.group_name)
              .join(', ') || '无'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="数据权限规则" size="small">
        <Tabs
          size="small"
          items={[
            {
              key: 'own_group',
              label: `组内权限 (${ownGroupApps.length})`,
              children: renderAppPermissionsTable(ownGroupApps),
            },
            {
              key: 'cross_group',
              label: `协作权限 (${crossGroupApps.length})`,
              children: renderAppPermissionsTable(crossGroupApps),
            },
          ]}
        />
      </Card>
    </div>
  );
}
