import { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar } from 'antd';
import {
  DashboardOutlined,
  AppstoreOutlined,
  SendOutlined,
  CheckCircleOutlined,
  SafetyCertificateOutlined,
  CloudServerOutlined,
  FileSearchOutlined,
  BoxPlotOutlined,
  BookOutlined,
  SettingOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CameraOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: 'apps-group', icon: <AppstoreOutlined />, label: '应用管理',
    children: [
      { key: '/apps', label: '应用列表' },
    ],
  },
  {
    key: 'releases-group',
    icon: <SendOutlined />,
    label: '发布管理',
    children: [
      { key: '/releases', label: '应用列表' },
    ],
  },
  {
    key: 'approvals-group',
    icon: <CheckCircleOutlined />,
    label: '审批中心',
    children: [
      { key: '/approvals/release', label: '发布审批' },
      { key: '/approvals', label: '权限审批' },
      { key: '/approvals/change', label: '变更审批' },
    ],
  },
  {
    key: 'permissions',
    icon: <SafetyCertificateOutlined />,
    label: '权限管理',
    children: [
      { key: '/permissions', label: '组织权限' },
      { key: '/permissions/my', label: '我的权限' },
      { key: '/permissions/apply', label: '权限申请' },
      { key: '/permissions/apply-records', label: '申请记录' },
      { key: '/permissions/related-to-me', label: '与我相关' },
      { key: '/permissions/approval-config', label: '审批配置' },
    ],
  },
  { key: '/artifacts', icon: <BoxPlotOutlined />, label: '制品管理' },
  { key: '/images', icon: <CameraOutlined />, label: '镜像管理' },
  {
    key: 'config',
    icon: <SettingOutlined />,
    label: '配置管理',
    children: [
      { key: '/config/templates', label: '配置模板' },
      { key: '/config/variables', label: '变量管理' },
      { key: '/config/releases', label: '配置发布记录' },
      {
        key: 'config-approval', label: '审核管理',
        children: [
          { key: '/config/approval/release-strategies', label: '发布策略' },
          { key: '/config/approval/permission-strategies', label: '权限策略' },
          { key: '/config/approval/templates', label: '审核模板' },
        ],
      },
    ],
  },
  { key: '/infrastructures', icon: <CloudServerOutlined />, label: '环境与集群' },
  { key: '/audit-logs', icon: <FileSearchOutlined />, label: '审计日志' },
  {
    key: 'knowledge',
    icon: <BookOutlined />,
    label: '知识库',
    children: [
      { key: '/knowledge/docs', label: '📚 系统文档' },
      { key: '/knowledge/interview', label: '📖 面试宝典' },
    ],
  },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // 找到当前选中的菜单项（使用完整路径匹配子菜单项）
  const selectedKey = location.pathname;

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="light" style={{ overflow: 'auto' }}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: collapsed ? 16 : 20,
          fontWeight: 'bold',
          borderBottom: '1px solid #f0f0f0',
        }}>
          {collapsed ? 'RS' : '发布系统 Demo'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={['permissions', 'config', 'knowledge', 'releases-group', 'approvals-group']}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ overflow: 'hidden' }}>
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          flexShrink: 0,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown
            menu={{
              items: [
                { key: 'profile', label: '我的权限', onClick: () => navigate('/permissions/my') },
                { type: 'divider' },
                { key: 'logout', label: '退出登录', onClick: logout },
              ],
            }}
          >
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.display_name || '未登录'}</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8, display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1, overflow: 'auto' }}>
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}