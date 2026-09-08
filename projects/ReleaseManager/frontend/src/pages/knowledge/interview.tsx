import { useEffect, useState } from 'react';
import {
  Typography, Card, Tag,
  Button, Spin,
} from 'antd';
import {
  ReadOutlined, LinkOutlined, WarningOutlined,
} from '@ant-design/icons';
import { knowledgeApi } from '../../api';

const { Title, Text } = Typography;

/* ============ 面试宝典页面 ============ */

export default function KnowledgeInterviewPage() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [embedError, setEmbedError] = useState(false);
  const [embedReady, setEmbedReady] = useState(false);
  const [embedTimedOut, setEmbedTimedOut] = useState(false);

  useEffect(() => {
    knowledgeApi.yuqueConfig().then((res: any) => {
      setConfig(res.data || res);
    }).catch(() => {
      setConfig({ configured: false });
    }).finally(() => setLoading(false));
  }, []);

  // 飞书文档 onLoad 可能不触发（跨域渐进加载），用定时器保底
  useEffect(() => {
    if (!config?.embed_enabled) return;
    const ready = setTimeout(() => setEmbedReady(true), 6000);
    const timeout = setTimeout(() => !embedReady && setEmbedTimedOut(true), 30000);
    return () => { clearTimeout(ready); clearTimeout(timeout); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config?.embed_enabled]);

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '80px 0' }}>
      <Spin size="large" />
      <div style={{ marginTop: 16, color: '#999' }}>加载中...</div>
    </div>
  );

  const { url, title, description, configured, embed_enabled } = config || {};
  const useEmbed = configured && embed_enabled;

  return (
    <>
      <style>{'.ant-layout-content { position: relative; }'}</style>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        background: '#fff',
      }}>
      {!configured ? (
        <Card style={{ borderRadius: 12, textAlign: 'center' }} styles={{ body: { padding: 40 } }}>
          <Tag color="orange" style={{ marginBottom: 12 }}>未配置</Tag>
          <Text type="secondary" style={{ display: 'block', fontSize: 13 }}>
            请在 <Text code>backend/knowledge/docs/yuque-config.json</Text> 中配置飞书文档链接
          </Text>
        </Card>
      ) : useEmbed ? (
        <div style={{ position: 'relative', flex: 1, minHeight: 0 }}>
          {/* 加载遮罩 */}
          {!embedReady && !embedError && (
            <div style={{
              position: 'absolute', inset: 0, zIndex: 10,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              background: '#fff',
            }}>
              {embedTimedOut ? (
                <>
                  <WarningOutlined style={{ fontSize: 32, color: '#faad14', marginBottom: 12 }} />
                  <div style={{ marginBottom: 16, color: '#666' }}>文档加载较慢，请尝试新窗口打开</div>
                  <Button type="primary" icon={<LinkOutlined />} href={url} target="_blank">
                    新窗口打开
                  </Button>
                </>
              ) : (
                <>
                  <Spin size="large" />
                  <div style={{ marginTop: 12, color: '#999' }}>正在加载飞书文档...</div>
                </>
              )}
            </div>
          )}

          {/* iframe 无边框无缝嵌入 */}
          <iframe
            src={url}
            style={{
              position: 'absolute', inset: 0,
              width: '100%', height: '100%',
              border: 'none', display: 'block',
            }}
            onLoad={() => setEmbedReady(true)}
          />

          {/* 加载失败回退 */}
          {embedError && (
            <Card style={{ borderRadius: 12, textAlign: 'center' }} styles={{ body: { padding: 40 } }}>
              <ReadOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
              <Title level={4} style={{ marginBottom: 8 }}>{title}</Title>
              <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
                无法直接预览文档内容
              </Text>
              <Button type="primary" size="large" icon={<LinkOutlined />} href={url} target="_blank" style={{ borderRadius: 8 }}>
                在新窗口打开
              </Button>
            </Card>
          )}
        </div>
      ) : (
        /* 新标签页模式 */
        <Card style={{ borderRadius: 12, textAlign: 'center' }} styles={{ body: { padding: 40 } }}>
          <ReadOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
          <Title level={4} style={{ marginBottom: 8 }}>{title || '面试宝典'}</Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
            {description || '包含各模块面试题、架构问答与实战场景分析'}
          </Text>
          <Button type="primary" size="large" icon={<LinkOutlined />} href={url} target="_blank" style={{ borderRadius: 8 }}>
            前往查看
          </Button>
        </Card>
      )}
    </div>
    </>
  );
}
