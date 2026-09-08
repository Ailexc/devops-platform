import { useEffect, useState } from 'react';
import {
  Typography, Table, Button, Modal, Form, Input, Select, message, Tag, Spin,
} from 'antd';
import { PlusOutlined, DiffOutlined } from '@ant-design/icons';
import { configApi, infraApi } from '../../api';

const { Title } = Typography;
const { TextArea } = Input;

interface ConfigRelease {
  id: number;
  template_id: number;
  template_name?: string;
  environment_id: number;
  environment_name?: string;
  version: string;
  rendered_content: string;
  status: string;
  creator_name: string;
  created_at: string;
}

interface Template {
  id: number;
  name: string;
  app_name: string;
}

interface Environment {
  id: number;
  name: string;
  code: string;
}

export default function ConfigReleaseListPage() {
  const [releases, setReleases] = useState<ConfigRelease[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(false);

  // Create release modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm] = Form.useForm();
  const [createLoading, setCreateLoading] = useState(false);
  const [previewContent, setPreviewContent] = useState('');

  // Diff modal
  const [diffModalOpen, setDiffModalOpen] = useState(false);
  const [diffContent, setDiffContent] = useState('');
  const [diffLoading, setDiffLoading] = useState(false);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      configApi.releases.list(),
      configApi.templates.list(),
      infraApi.environments.list(),
    ]).then(([releaseRes, templateRes, envRes]: any[]) => {
      setReleases(releaseRes.data || []);
      setTemplates(templateRes.data || []);
      setEnvironments(envRes?.data || []);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  // Create release
  const openCreateModal = () => {
    createForm.resetFields();
    setPreviewContent('');
    setCreateModalOpen(true);
  };

  const handleTemplateChange = async (templateId: number) => {
    const envId = createForm.getFieldValue('environment_id');
    if (templateId && envId) {
      try {
        const res: any = await configApi.templates.render(templateId, { environment_id: envId });
        setPreviewContent(res.data?.rendered_content || res.rendered_content || '');
      } catch {
        setPreviewContent('');
      }
    }
  };

  const handleEnvChange = async (envId: number) => {
    const templateId = createForm.getFieldValue('template_id');
    if (templateId && envId) {
      try {
        const res: any = await configApi.templates.render(templateId, { environment_id: envId });
        setPreviewContent(res.data?.rendered_content || res.rendered_content || '');
      } catch {
        setPreviewContent('');
      }
    }
  };

  const handleCreateRelease = async () => {
    try {
      const values = await createForm.validateFields();
      setCreateLoading(true);
      const res: any = await configApi.templates.render(values.template_id, {
        environment_id: values.environment_id,
      });
      const renderedContent = res.data?.rendered_content || res.rendered_content || '';
      await configApi.releases.create({
        template_id: values.template_id,
        environment_id: values.environment_id,
        rendered_content: renderedContent,
      });
      message.success('发布创建成功');
      setCreateModalOpen(false);
      loadData();
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('创建发布失败');
    } finally {
      setCreateLoading(false);
    }
  };

  // View diff
  const handleViewDiff = async (id: number) => {
    setDiffLoading(true);
    setDiffModalOpen(true);
    try {
      const res: any = await configApi.releases.diff(id);
      setDiffContent(res.data?.diff || res.diff || '无差异内容');
    } catch {
      setDiffContent('获取差异失败');
    } finally {
      setDiffLoading(false);
    }
  };

  const statusColors: Record<string, string> = {
    draft: 'default',
    published: 'green',
    rolled_back: 'orange',
    failed: 'red',
  };

  const columns = [
    { title: '模板名', dataIndex: 'template_name', key: 'template_name', width: 160 },
    { title: '环境', dataIndex: 'environment_name', key: 'environment_name', width: 100 },
    { title: '版本号', dataIndex: 'version', key: 'version', width: 100 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>{status}</Tag>
      ),
    },
    { title: '创建人', dataIndex: 'creator_name', key: 'creator_name', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: ConfigRelease) => (
        <Button
          type="link"
          size="small"
          icon={<DiffOutlined />}
          onClick={() => handleViewDiff(record.id)}
        >
          查看差异
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>配置发布记录</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          新建发布
        </Button>
      </div>

      <Table
        dataSource={releases}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
      />

      {/* Create release modal */}
      <Modal
        title="新建配置发布"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={handleCreateRelease}
        confirmLoading={createLoading}
        width={720}
        destroyOnHidden
      >
        <Form form={createForm} layout="vertical" preserve={false}>
          <Form.Item
            name="template_id"
            label="选择模板"
            rules={[{ required: true, message: '请选择模板' }]}
          >
            <Select
              placeholder="请选择模板"
              showSearch
              optionFilterProp="label"
              onChange={handleTemplateChange}
              options={templates.map((t) => ({
                value: t.id,
                label: `${t.name} (${t.app_name})`,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="environment_id"
            label="选择环境"
            rules={[{ required: true, message: '请选择环境' }]}
          >
            <Select
              placeholder="请选择环境"
              onChange={handleEnvChange}
              options={environments.map((e) => ({ value: e.id, label: e.name }))}
            />
          </Form.Item>
          {previewContent && (
            <Form.Item label="预览内容">
              <TextArea
                value={previewContent}
                readOnly
                rows={10}
                style={{ fontFamily: 'monospace', fontSize: 13 }}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* Diff modal */}
      <Modal
        title="配置差异对比"
        open={diffModalOpen}
        onCancel={() => setDiffModalOpen(false)}
        footer={null}
        width={800}
        destroyOnHidden
      >
        {diffLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
          </div>
        ) : (
          <TextArea
            value={diffContent}
            readOnly
            rows={20}
            style={{ fontFamily: 'monospace', fontSize: 13 }}
          />
        )}
      </Modal>
    </div>
  );
}