import { useEffect, useState } from 'react';
import {
  Typography, Card, Tag, Row, Col, Divider, Space,
  Button, Empty, Spin, message,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { knowledgeApi } from '../../api';

const { Title, Text } = Typography;

/* ============ Loading ============ */

const LoadingPage = () => (
  <div style={{ textAlign: 'center', padding: '80px 0' }}>
    <Spin size="large" />
    <div style={{ marginTop: 16, color: '#999' }}>加载中...</div>
  </div>
);

/* ============ Article Viewer ============ */

/**
 * 文章查看器。
 * 章节导航已内置于文章 HTML 自身（左侧目录 + 滚动高亮 + 折叠按钮），
 * 前端只负责用 iframe 原样渲染整份 HTML，不再解析/注入章节。
 *
 * iframe 撑满剩余视口高度，无边框、无圆角，营造"文档即页面"的沉浸体验。
 * 返回按钮与时间戳以浮动覆盖层形式展示，不占内容空间。
 */
const ArticleViewer = ({ article, onBack, initialAnchor }: {
  article: any;
  onBack: () => void;
  initialAnchor?: string;
}) => {
  // 若指定了初始锚点（如 s3），在文章内容末尾注入滚动脚本，iframe 加载后自动定位到该章节
  const content = initialAnchor
    ? article.content.replace(
        '</html>',
        `<script>window.addEventListener('DOMContentLoaded',function(){var el=document.getElementById('${initialAnchor}');if(el){window.setTimeout(function(){el.scrollIntoView();},120);}});<\/script></html>`,
      )
    : article.content;

  return (
    <div style={{
      flex: 1,
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      /* 负 margin 抵消外层 Content padding，使 iframe 撑满可视区 */
      margin: '-24px',
    }}>
      {/* 浮动工具栏 — 放在右侧，避免与 iframe 内左上角「📑 目录」按钮重叠 */}
      <div style={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        pointerEvents: 'none',
      }}>
        {article.updated && (
          <Text style={{ fontSize: 12, color: '#999', pointerEvents: 'auto' }}>
            🕐 {article.updated}
          </Text>
        )}
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          onClick={onBack}
          style={{ padding: '4px 10px', fontSize: 13, pointerEvents: 'auto',
            background: 'rgba(255,255,255,0.9)', borderRadius: 6,
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)' }}
        >
          返回目录
        </Button>
      </div>
      <iframe
        title={article.title}
        srcDoc={content}
        sandbox="allow-scripts"
        style={{
          width: '100%',
          flex: 1,
          minHeight: 0,
          border: 'none',
          borderRadius: 0,
          background: '#fff',
          display: 'block',
        }}
      />
    </div>
  );
};

/* ============ Module Detail ============ */

const ModuleDetail = ({ moduleId, onBack }: { moduleId: string; onBack: () => void }) => {
  const [mod, setMod] = useState<any>(null);
  const [articles, setArticles] = useState<any[]>([]);
  const [viewArticle, setViewArticle] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const articleParam = searchParams.get('article');
  const sectionParam = searchParams.get('section');

  useEffect(() => {
    setLoading(true);
    setViewArticle(null);
    knowledgeApi.moduleDetail(moduleId).then((res: any) => {
      const d = res.data || res;
      setMod(d);
      setArticles(d.articles || []);
      // URL 指定了文章 → 自动打开（可附带 section 锚点定位到具体章节）
      if (articleParam) {
        knowledgeApi.article(moduleId, articleParam).then((ares: any) => {
          setViewArticle(ares.data || ares);
        }).catch(() => {});
      }
    }).finally(() => setLoading(false));
  }, [moduleId]);

  if (loading) return <LoadingPage />;
  if (!mod) return <Empty description="模块不存在" />;
  if (viewArticle) return (
    <ArticleViewer
      article={viewArticle}
      onBack={() => setViewArticle(null)}
      initialAnchor={sectionParam || undefined}
    />
  );

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={onBack} style={{ padding: 0, marginBottom: 16 }}>返回</Button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <span style={{ fontSize: 32 }}>{mod.icon}</span>
        <div>
          <Title level={4} style={{ margin: 0 }}>{mod.name}</Title>
          <Text type="secondary">{mod.description}</Text>
        </div>
      </div>
      <Divider style={{ margin: '16px 0' }} />
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>共 {articles.length} 篇文章</Text>
      {articles.length === 0 ? (
        <Empty description="暂无文章" />
      ) : (
        <Row gutter={[16, 16]}>
          {articles.map((a: any) => (
            <Col xs={24} md={12} key={a.id}>
              <Card hoverable onClick={async () => {
                try {
                  const res: any = await knowledgeApi.article(moduleId, a.id);
                  setViewArticle(res.data || res);
                } catch { message.error('加载失败'); }
              }} style={{ borderRadius: 10, height: '100%' }} styles={{ body: { padding: 20 } }}>
                <Title level={5} style={{ marginTop: 0, marginBottom: 8 }}>{a.title}</Title>
                <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>{a.description}</Text>
                <Space size={4}>
                  {(a.tags || []).map((t: string) => <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>)}
                  {a.updated && <Text style={{ fontSize: 11, color: '#999' }}>🕐 {a.updated}</Text>}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

/* ============ Module Card ============ */

const ModuleCard = ({ mod, onClick }: { mod: any; onClick: () => void }) => (
  <Card hoverable onClick={onClick} style={{ borderRadius: 12, border: '1px solid #e2e5f0', height: '100%' }} styles={{ body: { padding: 24 } }}>
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
      <div style={{ width: 52, height: 52, borderRadius: 12, background: '#f6f8fa', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, flexShrink: 0 }}>{mod.icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Title level={5} style={{ margin: 0, marginBottom: 4 }}>{mod.name}</Title>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8, lineHeight: 1.5 }}>{mod.description}</Text>
        <Tag style={{ fontSize: 11, borderRadius: 10 }}>📄 {mod.article_count} 篇</Tag>
      </div>
    </div>
  </Card>
);

/* ============ 系统文档页面 ============ */

export default function KnowledgeDocsPage() {
  const [modules, setModules] = useState<any[]>([]);
  const [searchParams] = useSearchParams();
  const moduleParam = searchParams.get('module');
  const [selected, setSelected] = useState<string | null>(moduleParam);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    knowledgeApi.modules().then((res: any) => {
      setModules(res.data || []);
    }).finally(() => setLoading(false));
  }, []);

  if (selected) return <ModuleDetail moduleId={selected} onBack={() => setSelected(null)} />;
  if (loading) return <LoadingPage />;

  return (
    <div>
      {modules.length === 0 ? <Empty description="没有匹配的模块" /> : (
        <Row gutter={[20, 20]}>
          {modules.map((mod: any) => (
            <Col xs={24} sm={12} lg={8} key={mod.id}>
              <ModuleCard mod={mod} onClick={() => setSelected(mod.id)} />
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}
