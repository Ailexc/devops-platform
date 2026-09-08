import { Collapse, Alert } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

interface DocsSection {
  key: string;
  label: string;
  children: React.ReactNode;
}

interface DocsNoteProps {
  title: string;
  sections: DocsSection[];
  defaultActiveKey?: string[];
  type?: 'info' | 'warning' | 'success';
}

export default function DocsNote({ title, sections, defaultActiveKey, type = 'info' }: DocsNoteProps) {
  return (
    <Alert
      message={<strong><InfoCircleOutlined style={{ marginRight: 8 }} />{title}</strong>}
      description={
        <Collapse
          items={sections}
          defaultActiveKey={defaultActiveKey}
          size="small"
          style={{ background: 'transparent', border: 'none' }}
          ghost
        />
      }
      type={type}
      showIcon
      style={{ marginBottom: 16 }}
      closable
    />
  );
}