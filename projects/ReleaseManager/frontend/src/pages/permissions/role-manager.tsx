import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, Space, message, Typography } from 'antd';
import { authzApi } from '../../api';

const { Title } = Typography;

const ROLE_TYPES = [
  { value: 'admin', label: '管理员' },
  { value: 'deployer', label: '发布者' },
  { value: 'release_manager', label: '发布管理员' },
  { value: 'auditor', label: '审计员' },
  { value: 'viewer', label: '观察者' },
  { value: 'app_owner', label: '应用负责人' },
  { value: 'biz_owner', label: '业务线负责人' },
];

const ALL_PERMISSIONS = [
  { label: '菜单-仪表盘', value: 'menu_dashboard' },
  { label: '菜单-应用管理', value: 'menu_apps' },
  { label: '菜单-发布管理', value: 'menu_releases' },
  { label: '菜单-审批中心', value: 'menu_approvals' },
  { label: '菜单-权限管理', value: 'menu_permissions' },
  { label: '菜单-制品管理', value: 'menu_artifacts' },
  { label: '菜单-配置管理', value: 'menu_config' },
  { label: '菜单-环境与集群', value: 'menu_infrastructures' },
  { label: '菜单-部署历史', value: 'menu_deploy_history' },
  { label: '菜单-审计日志', value: 'menu_audit_logs' },
  { label: '操作-创建应用', value: 'action_create_app' },
  { label: '操作-创建发布', value: 'action_create_release' },
  { label: '操作-审批', value: 'action_approve' },
  { label: '操作-回滚', value: 'action_rollback' },
  { label: '操作-管理权限', value: 'action_manage_permission' },
];

export default function RoleManagerPage() {
  const [roles, setRoles] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = () => {
    authzApi.roles.list().then((res: any) => setRoles(res.data || []));
  };

  const handleSave = async (values: any) => {
    try {
      if (editingRole) {
        await authzApi.roles.update(editingRole.id, values);
        message.success('角色更新成功');
      } else {
        await authzApi.roles.create(values);
        message.success('角色创建成功');
      }
      setModalOpen(false);
      form.resetFields();
      setEditingRole(null);
      loadRoles();
    } catch (err) {
      message.error('操作失败');
    }
  };

  const handleDelete = (role: any) => {
    if (role.is_system) {
      message.warning('系统内置角色不可删除');
      return;
    }
    Modal.confirm({
      title: `确认删除角色 "${role.name}"？`,
      onOk: async () => {
        await authzApi.roles.delete(role.id);
        message.success('已删除');
        loadRoles();
      },
    });
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '编码', dataIndex: 'code', key: 'code' },
    {
      title: '内置',
      dataIndex: 'is_system',
      key: 'is_system',
      render: (v: boolean) => v ? <Tag color="blue">系统</Tag> : <Tag>自定义</Tag>,
    },
    {
      title: '权限数',
      key: 'perm_count',
      render: (_: any, record: any) => record.permission_codes?.length || 0,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => {
            setEditingRole(record);
            form.setFieldsValue(record);
            setModalOpen(true);
          }}>
            编辑
          </Button>
          <Button type="link" danger size="small" onClick={() => handleDelete(record)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>角色管理</Title>
        <Button type="primary" onClick={() => {
          setEditingRole(null);
          form.resetFields();
          setModalOpen(true);
        }}>
          创建角色
        </Button>
      </div>
      <Table dataSource={roles} columns={columns} rowKey="id" size="small" />

      <Modal
        title={editingRole ? '编辑角色' : '创建角色'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item name="name" label="角色名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="角色编码" rules={[{ required: true }]}>
            <Select options={editingRole ? undefined : ROLE_TYPES} disabled={editingRole} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="permission_codes" label="功能权限">
            <Select mode="multiple" options={ALL_PERMISSIONS} placeholder="选择权限" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}