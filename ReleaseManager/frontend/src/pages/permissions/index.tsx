import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row, Col, Card, Tree, Typography, Descriptions, Tag, Table, Button,
  message, Input, Space, Divider, Tabs, Collapse, Tooltip, Empty,
} from 'antd';
import {
  ShareAltOutlined, PlusOutlined, StopOutlined, SettingOutlined,
  RollbackOutlined,
} from '@ant-design/icons';
import { orgApi, authzApi, appApi, infraApi } from '../../api';
import PermissionAdjustDrawer from './PermissionAdjustDrawer';
import type { DataNode } from 'antd/es/tree';

const { Title, Text } = Typography;
const { Panel } = Collapse;

const ENV_TYPE_TAG_COLORS: Record<string, string> = {
  dev: 'green',
  test: 'blue',
  staging: 'orange',
  prod: 'red',
};

const ENV_TYPE_LABELS: Record<string, string> = {
  dev: '开发',
  test: '测试',
  staging: '预发',
  prod: '生产',
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

interface RuleItem {
  id: number;
  role_id?: number;
  app_id: number;
  app_name: string;
  env_type: string;
  env_type_label: string;
  is_all_envs: boolean;
  allow_env_ids: number[];
  deny_env_ids: number[];
  grant_scope: 'own_group' | 'cross_group';
  grant_scope_label: string;
  valid_from?: string;
  valid_to?: string;
}

interface EnvPermission {
  env_type: string;
  env_type_label: string;
  scope: 'all' | 'partial' | 'none';
  allowed_envs: EnvInfo[];
  unauthorized_envs: EnvInfo[];
  denied_envs: EnvInfo[];
  env_details: EnvDetail[];
  permission_source: 'group' | 'personal' | 'mixed' | 'cross';
  permission_source_label: string;
  is_shared_out: boolean;
}

interface EnvDetail {
  id: number;
  name: string;
  code: string;
  env_type: string;
  status: 'allowed' | 'denied' | 'unauthorized';
}

interface AppPermission {
  app_id: number;
  app_name: string;
  app_code: string;
  business_line_name: string;
  owner_group_name: string;
  env_permissions: EnvPermission[];
}

interface GroupedRule {
  app_id: number;
  app_name: string;
  app_code: string;
  env_type: string;
  env_type_label: string;
  is_all_envs: boolean;
  allow_env_ids: number[];
  deny_env_ids: number[];
  grant_scope: 'own_group' | 'cross_group';
  is_shared_out: boolean;
  rule_ids: number[];
}

const envTypeOrder = (envType: string) => {
  const order = ['dev', 'test', 'staging', 'prod'];
  return order.indexOf(envType) === -1 ? 99 : order.indexOf(envType);
};

export default function PermissionIndexPage() {
  const navigate = useNavigate();

  const [treeData, setTreeData] = useState<DataNode[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [nodeType, setNodeType] = useState<string>('');
  const [groupPermissions, setGroupPermissions] = useState<any>(null);
  const [userPermissions, setUserPermissions] = useState<any>(null);
  const [searchValue, setSearchValue] = useState('');
  const [nodeMap, setNodeMap] = useState<Map<string, any>>(new Map());
  const [apps, setApps] = useState<any[]>([]);
  const [envs, setEnvs] = useState<EnvInfo[]>([]);
  const [activeGroupTab, setActiveGroupTab] = useState('own');
  const [activeUserTab, setActiveUserTab] = useState('own_group');

  // 权限调整抽屉
  const [adjustDrawerOpen, setAdjustDrawerOpen] = useState(false);
  const [adjustDrawerParams, setAdjustDrawerParams] = useState<{
    groupId: number; appId: number; appName: string; envType: string;
  } | null>(null);

  useEffect(() => {
    loadTree();
    loadApps();
    loadEnvs();
  }, []);

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

  const loadTree = () => {
    orgApi.tree().then((res: any) => {
      const data = res.data || [];
      const map = new Map<string, any>();
      const converted = convertToTreeData(data, '', map);
      setTreeData(converted);
      setNodeMap(map);
    });
  };

  const convertToTreeData = (nodes: any[], parentKey?: string, map?: Map<string, any>): DataNode[] => {
    return nodes.map((n: any) => {
      const key = parentKey ? `${parentKey}-${n.type}_${n.id}` : `${n.type}_${n.id}`;
      if (map) map.set(key, n);
      const accessible = n.accessible !== false;
      let title = n.name;
      if (n.type === 'user' && n.is_leader) {
        title = `${n.name} 👑`;
      }
      // 不可访问的节点显示灰色
      if (!accessible && n.type !== 'user') {
        title = `${title}`;
      }
      return {
        key,
        title,
        icon: getIcon(n.type),
        isLeaf: n.type === 'user',
        className: accessible ? '' : 'tree-node-inaccessible',
        children: n.children ? convertToTreeData(n.children, key, map) : undefined,
        data: n,
      };
    });
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'business_line': return '🏢';
      case 'group': return '👥';
      case 'user': return '👤';
      default: return '📄';
    }
  };

  useEffect(() => {
    if (selectedKeys.length === 0) {
      setSelectedNode(null);
      setGroupPermissions(null);
      setUserPermissions(null);
      return;
    }

    const key = String(selectedKeys[0]);
    const nodeData = nodeMap.get(key);
    if (!nodeData) return;

    setSelectedNode(nodeData);
    setNodeType(nodeData.type);
    setGroupPermissions(null);
    setUserPermissions(null);

    if (nodeData.type === 'group') {
      authzApi.groupPermissions(nodeData.id).then((res: any) => {
        setGroupPermissions(res.data);
      }).catch(() => {});
    }

    if (nodeData.type === 'user') {
      authzApi.userPermissions(nodeData.id).then((res: any) => {
        setUserPermissions(res.data);
      }).catch(() => {});
    }
  }, [selectedKeys, nodeMap]);

  const handleSelect = (keys: React.Key[]) => {
    setSelectedKeys(keys);
  };

  const filterTree = (nodes: any[]): any[] => {
    if (!searchValue) return nodes;
    return nodes
      .map((n) => ({ ...n, children: n.children ? filterTree(n.children) : n.children }))
      .filter((n) => {
        const match = n.name?.includes(searchValue);
        return match || (n.children && n.children.length > 0);
      });
  };

  const filteredTree = filterTree(treeData);

  const getEnvListByType = (envType: string) => {
    return envs.filter((e) => e.env_type === envType);
  };

  // 按应用+环境类型对组规则分组
  // 本组应用权限 Tab = own_group + 本组分享出去的 cross_group
  // 协作应用权限 Tab = 其他组分享给本组的 cross_group
  const groupedGroupRules = useMemo(() => {
    const rules: RuleItem[] = groupPermissions?.own_rules || [];
    const groupRoleId = groupPermissions?.group_role_id;
    const map = new Map<string, GroupedRule>();

    rules.forEach((r) => {
      const isSharedOut = r.grant_scope === 'cross_group' && r.role_id !== groupRoleId;
      const key = `${r.app_id}-${r.env_type}-${r.grant_scope}-${isSharedOut ? 'out' : 'in'}`;
      if (!map.has(key)) {
        map.set(key, {
          app_id: r.app_id,
          app_name: r.app_name,
          app_code: apps.find((a) => a.id === r.app_id)?.code || r.app_name,
          env_type: r.env_type,
          env_type_label: r.env_type_label,
          is_all_envs: r.is_all_envs,
          allow_env_ids: [],
          deny_env_ids: [],
          grant_scope: r.grant_scope,
          is_shared_out: isSharedOut,
          rule_ids: [],
        });
      }
      const item = map.get(key)!;
      item.rule_ids.push(r.id);
      if (r.is_all_envs) {
        item.is_all_envs = true;
      }
      item.allow_env_ids = Array.from(new Set([...item.allow_env_ids, ...(r.allow_env_ids || [])]));
      item.deny_env_ids = Array.from(new Set([...item.deny_env_ids, ...(r.deny_env_ids || [])]));
    });

    // 按应用分组
    const appMap = new Map<number, GroupedRule[]>();
    map.forEach((item) => {
      if (!appMap.has(item.app_id)) appMap.set(item.app_id, []);
      appMap.get(item.app_id)!.push(item);
    });

    return Array.from(appMap.entries()).map(([app_id, items]) => ({
      app_id,
      app_name: items[0].app_name,
      app_code: items[0].app_code,
      env_types: items.sort((a, b) => envTypeOrder(a.env_type) - envTypeOrder(b.env_type)),
    }));
  }, [groupPermissions, apps]);

  const buildEnvPermissionForGroupRule = (rule: GroupedRule): EnvPermission => {
    const allEnvs = getEnvListByType(rule.env_type);
    const allowedIds = new Set(rule.is_all_envs ? allEnvs.map((e) => e.id) : rule.allow_env_ids);
    const deniedIds = new Set(rule.deny_env_ids || []);

    const allowed = allEnvs.filter((e) => allowedIds.has(e.id) && !deniedIds.has(e.id));
    const denied = allEnvs.filter((e) => deniedIds.has(e.id));
    const unauthorized = allEnvs.filter((e) => !allowedIds.has(e.id) && !deniedIds.has(e.id));

    const envDetails: EnvDetail[] = [
      ...allowed.map((e) => ({ ...e, status: 'allowed' as const })),
      ...denied.map((e) => ({ ...e, status: 'denied' as const })),
      ...unauthorized.map((e) => ({ ...e, status: 'unauthorized' as const })),
    ];

    let scope: 'all' | 'partial' | 'none' = 'none';
    if (allEnvs.length > 0 && allowed.length === allEnvs.length && denied.length === 0) {
      scope = 'all';
    } else if (allowed.length > 0) {
      scope = 'partial';
    }

    let source: 'group' | 'personal' | 'cross' = 'group';
    let label = '团队权限（组内）';
    if (rule.grant_scope === 'cross_group') {
      source = 'cross';
      label = rule.is_shared_out ? '团队权限（组外协作）' : '团队权限（组外协作）';
    }

    return {
      env_type: rule.env_type,
      env_type_label: rule.env_type_label,
      scope,
      allowed_envs: allowed,
      unauthorized_envs: unauthorized,
      denied_envs: denied,
      env_details: envDetails,
      permission_source: source,
      permission_source_label: label,
      is_shared_out: rule.is_shared_out,
    };
  };

  const handleShare = () => {
    navigate(`/permissions/share?groupId=${selectedNode.id}`);
  };

  const handleApply = () => {
    navigate(`/permissions/apply?groupId=${selectedNode.id}&mode=apply`);
  };

  const renderEnvStatusTag = (status: EnvDetail['status']) => {
    if (status === 'allowed') return <Tag color="green">已授权</Tag>;
    if (status === 'denied') return <Tag color="red">已拒绝</Tag>;
    return <Tag>未授权</Tag>;
  };

  const renderEnvDetailActions = (
    app: any,
    envPerm: EnvPermission,
    viewContext: 'group' | 'user',
    _tabType: 'own' | 'cross'
  ) => {
    if (viewContext !== 'group') return null;
    const canManage = selectedNode?.available_actions?.includes('manage');
    const handleClick = () => {
      setAdjustDrawerParams({
        groupId: selectedNode.id,
        appId: app.app_id,
        appName: app.app_name,
        envType: envPerm.env_type,
      });
      setAdjustDrawerOpen(true);
    };
    return (
      <Tooltip title={!canManage ? '仅组负责人可调整权限' : undefined}>
        <Button size="small" disabled={!canManage} onClick={canManage ? handleClick : undefined}>
          权限调整
        </Button>
      </Tooltip>
    );
  };

  const renderEnvDetailTable = (app: any, envPerm: EnvPermission, tabType: 'own' | 'cross') => {
    const cloudProviderLabels: Record<string, string> = {
      aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', huawei: '华为云', azure: 'Azure', gcp: 'GCP',
    };

    return (
      <Table
        dataSource={envPerm.env_details || []}
        columns={[
          { title: '环境名称', dataIndex: 'name', key: 'name', width: 140 },
          { title: '环境编码', dataIndex: 'code', key: 'code', width: 120, render: (v: string) => <Tag color="default" style={{ fontSize: '10px' }}>{v}</Tag> },
          { title: '环境类型', dataIndex: 'env_type', key: 'env_type', width: 100, render: (v: string) => <Tag color={ENV_TYPE_TAG_COLORS[v] || 'default'}>{ENV_TYPE_LABELS[v] || v}</Tag> },
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
            title: '状态',
            key: 'status',
            width: 100,
            render: (_: any, record: EnvDetail) => renderEnvStatusTag(record.status),
          },
          {
            title: '权限来源',
            key: 'source',
            width: 120,
            render: (_: any, record: EnvDetail) => {
              if (record.status !== 'allowed') return <Text type="secondary">-</Text>;
              const source = record.permission_source;
              const label = source === 'personal' ? '个人申请' : source === 'mixed' ? '混合' : '团队继承';
              return <Tag color={source === 'personal' ? 'purple' : source === 'mixed' ? 'magenta' : 'blue'} style={{ fontSize: '10px' }}>{label}</Tag>;
            },
          },
        ]}
        rowKey="id"
        size="small"
        pagination={false}
      />
    );
  };

  const renderEnvTypeTable = (app: any, envPerms: EnvPermission[], tabType: 'own' | 'cross') => {
    if (envPerms.length === 0) {
      return <Text type="secondary">暂无环境权限</Text>;
    }

    return (
      <div style={{ padding: '8px 16px', background: '#fafafa', borderRadius: 8 }}>
        <div style={{ fontWeight: 500, marginBottom: 12 }}>环境权限详情</div>
        <Table
          dataSource={envPerms}
          columns={[
            {
              title: '环境类型',
              dataIndex: 'env_type_label',
              key: 'env_type',
              width: 110,
              render: (v: string, record: EnvPermission) => (
                <Tag color={ENV_TYPE_TAG_COLORS[record.env_type] || 'default'}>{v}</Tag>
              ),
            },
            {
              title: '授权范围',
              key: 'scope',
              width: 110,
              render: (_: any, record: EnvPermission) => {
                if (record.scope === 'all') return <Tag color="green">全部授权</Tag>;
                if (record.scope === 'partial') return <Tag color="blue">部分授权</Tag>;
                return <Tag>未授权</Tag>;
              },
            },
            {
              title: '环境数量',
              key: 'env_count',
              width: 100,
              render: (_: any, record: EnvPermission) => `${(record.env_details || []).length} 个`,
            },
            {
              title: '授权比例',
              key: 'auth_ratio',
              width: 100,
              render: (_: any, record: EnvPermission) => {
                const details = record.env_details || [];
                const allowed = details.filter((e) => e.status === 'allowed').length;
                return `${allowed}/${details.length}`;
              },
            },
            {
            title: '权限属性',
            key: 'permission_source',
            width: 140,
            render: (_: any, record: EnvPermission) => (
              <Tag color={
                record.permission_source === 'personal' ? 'purple' :
                record.permission_source === 'mixed' ? 'magenta' :
                record.permission_source === 'cross' ? 'orange' : 'blue'
              }>
                {record.permission_source_label}
              </Tag>
            ),
          },
          {
            title: '权限调整',
            key: 'action',
            width: 180,
            render: (_: any, record: EnvPermission) => renderEnvDetailActions(app, record, 'group', tabType),
          },
          ]}
          expandable={{
            expandedRowRender: (record: EnvPermission) => renderEnvDetailTable(app, record, tabType),
            rowExpandable: () => true,
          }}
          rowKey={(record: EnvPermission) => `${record.env_type}-${record.permission_source}`}
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  const renderGroupAppPanel = (tabType: 'own' | 'cross') => {
    const grouped = groupedGroupRules.filter((app) =>
      app.env_types.some((et) =>
        tabType === 'own'
          ? et.grant_scope === 'own_group' || (et.grant_scope === 'cross_group' && et.is_shared_out)
          : et.grant_scope === 'cross_group' && !et.is_shared_out
      )
    );

    if (grouped.length === 0) {
      return <Text type="secondary">暂无{tabType === 'own' ? '本组' : '协作'}应用权限</Text>;
    }

    const dataSource = grouped.map((app) => {
      const appInfo = apps.find((a) => a.id === app.app_id) || {};
      const envPerms = app.env_types
        .filter((et) =>
          tabType === 'own'
            ? et.grant_scope === 'own_group' || (et.grant_scope === 'cross_group' && et.is_shared_out)
            : et.grant_scope === 'cross_group' && !et.is_shared_out
        )
        .map(buildEnvPermissionForGroupRule);
      const allowedCount = envPerms.reduce(
        (sum, ep) => sum + ep.env_details.filter((e) => e.status === 'allowed').length,
        0
      );
      const totalCount = envPerms.reduce((sum, ep) => sum + ep.env_details.length, 0);
      return {
        ...app,
        appInfo,
        envPerms,
        authorized_count: `${allowedCount}/${totalCount}`,
      };
    });

    const appTypeMap: Record<string, string> = {
      web: 'Web 应用', backend: '后端服务', mobile: '移动应用', middleware: '中间件',
      job: '定时任务', data: '数据服务', other: '其他',
    };
    const languageMap: Record<string, string> = {
      python: 'Python', go: 'Go', node: 'Node.js', java: 'Java', rust: 'Rust',
      php: 'PHP', dotnet: '.NET', other: '其他',
    };

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
            width: 140,
            render: (_: any, record: any) => (
              <Space>
                <Tag color="blue">{appTypeMap[record.appInfo.app_type] || record.appInfo.app_type || '-'}</Tag>
                <Tag color="default" style={{ fontSize: '10px' }}>{languageMap[record.appInfo.language] || record.appInfo.language || '-'}</Tag>
              </Space>
            ),
          },
          {
            title: '负责人',
            key: 'owner',
            width: 100,
            render: (_: any, record: any) => record.appInfo.owner_name || record.appInfo.owner?.display_name || '-',
          },
          {
            title: '承接组',
            key: 'owner_group',
            width: 140,
            render: (_: any, record: any) => record.appInfo.owner_group_name || record.appInfo.owner_group?.name || '-',
          },
          {
            title: '业务线',
            key: 'business_line',
            width: 110,
            render: (_: any, record: any) => record.appInfo.business_line_name || record.appInfo.business_line?.name || '-',
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
            width: 90,
            render: (_: any, record: any) => <Tag color="default">{record.authorized_count}</Tag>,
          },
        ]}
        expandable={{
          expandedRowRender: (record: any) => renderEnvTypeTable(record, record.envPerms, tabType),
          rowExpandable: () => true,
        }}
        rowKey="app_id"
        size="small"
        pagination={false}
      />
    );
  };

  // 用户视图：应用 -> 环境类型 -> 环境详情（列表展开风格）
  const renderUserEnvDetailTable = (app: any, envPerm: EnvPermission) => {
    const cloudProviderLabels: Record<string, string> = {
      aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', huawei: '华为云', azure: 'Azure', gcp: 'GCP',
    };

    return (
      <Table
        dataSource={envPerm.env_details || []}
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
            title: '状态',
            key: 'status',
            width: 100,
            render: (_: any, record: EnvDetail) => renderEnvStatusTag(record.status),
          },
          {
            title: '权限来源',
            key: 'source',
            width: 120,
            render: (_: any, record: EnvDetail) => {
              if (record.status !== 'allowed') return <Text type="secondary">-</Text>;
              const source = record.permission_source;
              const label = source === 'personal' ? '个人申请' : source === 'mixed' ? '混合' : '团队继承';
              return <Tag color={source === 'personal' ? 'purple' : source === 'mixed' ? 'magenta' : 'blue'} style={{ fontSize: '10px' }}>{label}</Tag>;
            },
          },
        ]}
        rowKey="id"
        size="small"
        pagination={false}
      />
    );
  };

  const renderUserEnvTypeTable = (app: any, envPerms: EnvPermission[]) => {
    if (envPerms.length === 0) {
      return <Text type="secondary">暂无环境权限</Text>;
    }

    return (
      <div style={{ padding: '8px 16px', background: '#fafafa', borderRadius: 8 }}>
        <div style={{ fontWeight: 500, marginBottom: 12 }}>环境权限详情</div>
        <Table
          dataSource={envPerms}
          columns={[
            {
              title: '环境类型',
              dataIndex: 'env_type_label',
              key: 'env_type',
              width: 110,
              render: (v: string, record: EnvPermission) => (
                <Tag color={ENV_TYPE_TAG_COLORS[record.env_type] || 'default'}>{v}</Tag>
              ),
            },
            {
              title: '授权范围',
              key: 'scope',
              width: 110,
              render: (_: any, record: EnvPermission) => {
                if (record.scope === 'all') return <Tag color="green">全部授权</Tag>;
                if (record.scope === 'partial') return <Tag color="blue">部分授权</Tag>;
                return <Tag>未授权</Tag>;
              },
            },
            {
              title: '环境数量',
              key: 'env_count',
              width: 100,
              render: (_: any, record: EnvPermission) => `${(record.env_details || []).length} 个`,
            },
            {
              title: '授权比例',
              key: 'auth_ratio',
              width: 100,
              render: (_: any, record: EnvPermission) => {
                const details = record.env_details || [];
                const allowed = details.filter((e) => e.status === 'allowed').length;
                return `${allowed}/${details.length}`;
              },
            },
            {
              title: '权限属性',
              key: 'permission_source',
              width: 140,
              render: (_: any, record: EnvPermission) => (
                <Tag color={
                  record.permission_source === 'personal' ? 'purple' :
                  record.permission_source === 'mixed' ? 'magenta' :
                  record.permission_source === 'cross' ? 'orange' : 'blue'
                }>
                  {record.permission_source_label}
                </Tag>
              ),
            },
          ]}
          expandable={{
            expandedRowRender: (record: EnvPermission) => renderUserEnvDetailTable(app, record),
            rowExpandable: () => true,
          }}
          rowKey={(record: EnvPermission) => `${record.env_type}-${record.permission_source}`}
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  const renderUserAppPermissionsPanel = (appList: AppPermission[]) => {
    if (!appList || appList.length === 0) return <Text type="secondary">暂无权限</Text>;

    const dataSource = appList.map((app) => {
      const appInfo = apps.find((a) => a.id === app.app_id) || {};
      const envPerms = app.env_permissions || [];
      const allowedCount = envPerms.reduce(
        (sum, ep) => sum + (ep.allowed_envs || []).length,
        0
      );
      const totalCount = envPerms.reduce(
        (sum, ep) => sum + (ep.allowed_envs || []).length + (ep.unauthorized_envs || []).length + (ep.denied_envs || []).length,
        0
      );
      return { ...app, appInfo, envPerms, authorized_count: `${allowedCount}/${totalCount}` };
    });

    const appTypeMap: Record<string, string> = {
      web: 'Web 应用', backend: '后端服务', mobile: '移动应用', middleware: '中间件',
      job: '定时任务', data: '数据服务', other: '其他',
    };
    const languageMap: Record<string, string> = {
      python: 'Python', go: 'Go', node: 'Node.js', java: 'Java', rust: 'Rust',
      php: 'PHP', dotnet: '.NET', other: '其他',
    };
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
                <Tag color="blue">{appTypeMap[record.appInfo.app_type] || record.appInfo.app_type || '-'}</Tag>
                <Tag color="default" style={{ fontSize: '10px' }}>{languageMap[record.appInfo.language] || record.appInfo.language || '-'}</Tag>
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
          expandedRowRender: (record: any) => renderUserEnvTypeTable(record, record.envPerms),
          rowExpandable: () => true,
        }}
        rowKey="app_id"
        size="small"
        pagination={false}
      />
    );
  };

  // ── 操作按钮组渲染 ──
  // 所有按钮统一风格：size=small，管理类 default，操作类 primary
  // 无权限时 disabled + Tooltip 说明原因
  const renderActionButtons = (node: any) => {
    const actions = node.available_actions || [];
    const btns: React.ReactNode[] = [];

    // 管理类按钮（需特定上下文，权限调整在环境详情行内处理）
    if (actions.includes('revoke')) {
      btns.push(
        <Button key="revoke" size="small" icon={<RollbackOutlined />}
          onClick={() => navigate(`/permissions/revoke?groupId=${node.id}`)}>
          回收协作
        </Button>
      );
    } else if (node.accessible && node.type === 'group') {
      btns.push(
        <Tooltip key="revoke-disabled" title="仅组成员可回收">
          <Button size="small" icon={<RollbackOutlined />} disabled>回收协作</Button>
        </Tooltip>
      );
    }

    return btns;
  };

  // 回收协作权限弹窗（仅针对本组分享出去的 cross_group 规则）

  return (
    <div>
      <style>{`
        .tree-node-inaccessible .ant-tree-node-content-wrapper {
          opacity: 0.55;
        }
        .tree-node-inaccessible .ant-tree-node-content-wrapper:hover {
          opacity: 0.75;
        }
      `}</style>
      <Title level={4}>组织权限</Title>
      <Row gutter={16}>
        <Col span={7}>
          <Card title="组织树" size="small">
            <Input.Search
              placeholder="搜索用户/组"
              style={{ marginBottom: 8 }}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
            <Tree
              treeData={filteredTree}
              onSelect={handleSelect}
              selectedKeys={selectedKeys}
              showIcon
              defaultExpandAll
            />
          </Card>
        </Col>
        <Col span={17}>
          {/* ── 无权查看占位 ── */}
          {selectedNode && selectedNode.accessible === false && (
            <Card size="small" style={{ backgroundColor: '#fffbe6', border: '1px solid #ffe58f' }}>
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <StopOutlined style={{ fontSize: 56, color: '#faad14' }} />
                <div style={{ marginTop: 16, fontSize: 16, color: '#ad6800' }}>
                  您没有权限查看此{nodeType === 'business_line' ? '业务线' : nodeType === 'group' ? '组' : '用户'}的详情
                </div>
                <div style={{ marginTop: 8, fontSize: 13, color: '#8c6b00' }}>
                  如需访问，请联系相关负责人
                </div>
              </div>
            </Card>
          )}

          {/* ── 业务线节点（无权时跳过 ── */}
          {selectedNode && selectedNode.accessible !== false && nodeType === 'business_line' && (
            <Card title={`业务线: ${selectedNode.name}`} size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="编码">{selectedNode.code}</Descriptions.Item>
                <Descriptions.Item label="组数量">{selectedNode.children?.length || 0}</Descriptions.Item>
                <Descriptions.Item label="负责人">
                  {selectedNode.leader_name ? (
                    <Tag color="blue">{selectedNode.leader_name}</Tag>
                  ) : (
                    <Text type="secondary">未设置</Text>
                  )}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* ── 组节点（无权时跳过） ── */}
          {selectedNode && selectedNode.accessible !== false && nodeType === 'group' && (
            <Card title={`组: ${selectedNode.name}`} size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="编码">{selectedNode.code}</Descriptions.Item>
                <Descriptions.Item label="成员数">{selectedNode.children?.length || 0}</Descriptions.Item>
                <Descriptions.Item label="组负责人">
                  {selectedNode.leader_name ? (
                    <Tag color="blue">{selectedNode.leader_name}</Tag>
                  ) : (
                    <Text type="secondary">未设置</Text>
                  )}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              {selectedNode.available_actions && selectedNode.available_actions.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                  {renderActionButtons(selectedNode)}
                  {selectedNode.available_actions.includes('share') ? (
                    <Button type="primary" size="small" icon={<ShareAltOutlined />} onClick={handleShare}>
                      分享协作
                    </Button>
                  ) : selectedNode.accessible && (
                    <Tooltip title="仅组成员可发起分享">
                      <Button type="primary" size="small" icon={<ShareAltOutlined />} disabled>
                        分享协作
                      </Button>
                    </Tooltip>
                  )}
                  {selectedNode.available_actions.includes('apply') ? (
                    <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleApply}>
                      申请权限
                    </Button>
                  ) : selectedNode.accessible && (
                    <Tooltip title="仅组成员可申请">
                      <Button type="primary" size="small" icon={<PlusOutlined />} disabled>
                        申请权限
                      </Button>
                    </Tooltip>
                  )}
                </div>
              )}

              <Tabs
                size="small"
                activeKey={activeGroupTab}
                onChange={setActiveGroupTab}
                items={[
                  {
                    key: 'own',
                    label: '本组应用权限',
                    children: (
                      <>
                        <div style={{ marginBottom: 16 }}>
                          <Text type="secondary">
                            展示本组负责的应用，以及本组成员/组外协作人员在这些应用下的权限情况。
                          </Text>
                        </div>
                        {renderGroupAppPanel('own')}
                      </>
                    ),
                  },
                  {
                    key: 'cross',
                    label: '协作应用权限',
                    children: (
                      <>
                        <div style={{ marginBottom: 16 }}>
                          <Text type="secondary">
                            展示其他组授权给本组协作使用的应用。
                          </Text>
                        </div>
                        {renderGroupAppPanel('cross')}
                      </>
                    ),
                  },
                ]}
              />
            </Card>
          )}

          {/* ── 用户节点（无权时跳过） ── */}
          {selectedNode && selectedNode.accessible !== false && nodeType === 'user' && (
            <Card title={`用户: ${selectedNode.name}`} size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="用户名">{selectedNode.code}</Descriptions.Item>
                <Descriptions.Item label="成员类型">
                  <Tag color={selectedNode.membership_type === 'primary' ? 'blue' : 'orange'}>
                    {selectedNode.membership_type === 'primary' ? '归属' : '协作'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>

              {userPermissions && (
                <>
                  <Divider />
                  <Title level={5}>所属组</Title>
                  <Space>
                    {userPermissions.groups?.map((g: any) => (
                      <Tag key={g.group_id} color={g.membership_type === 'primary' ? 'blue' : 'orange'}>
                        {g.group_name} ({g.membership_type === 'primary' ? '归属' : '协作'})
                      </Tag>
                    ))}
                  </Space>

                  <Divider />
                  <Tabs
                    size="small"
                    activeKey={activeUserTab}
                    onChange={setActiveUserTab}
                    items={[
                      {
                        key: 'own_group',
                        label: `组内权限 (${(userPermissions.own_group_apps || []).length})`,
                        children: renderUserAppPermissionsPanel(userPermissions.own_group_apps || []),
                      },
                      {
                        key: 'cross_group',
                        label: `协作权限 (${(userPermissions.cross_group_apps || []).length})`,
                        children: renderUserAppPermissionsPanel(userPermissions.cross_group_apps || []),
                      },
                    ]}
                  />
                </>
              )}
            </Card>
          )}

          {!selectedNode && (
            <Card size="small">
              <Text type="secondary">请从左侧组织树中选择一个节点查看详情</Text>
            </Card>
          )}
        </Col>
      </Row>

      {/* 权限调整抽屉 */}
      {adjustDrawerParams && (
        <PermissionAdjustDrawer
          open={adjustDrawerOpen}
          groupId={adjustDrawerParams.groupId}
          appId={adjustDrawerParams.appId}
          appName={adjustDrawerParams.appName}
          envType={adjustDrawerParams.envType}
          onClose={() => {
            setAdjustDrawerOpen(false);
            setAdjustDrawerParams(null);
          }}
          onSuccess={() => {
            // 刷新组权限数据
            if (selectedNode?.type === 'group') {
              authzApi.groupPermissions(selectedNode.id).then((res: any) => {
                setGroupPermissions(res.data);
              }).catch(() => {});
            }
          }}
        />
      )}
    </div>
  );
}
