import { useEffect, useState, useRef } from 'react';
import {
  Card, Descriptions, Tag, Typography, Space, Spin, Button, Timeline, message, Modal,
} from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { releaseApi, configApi } from '../../api';

const { Title, Text } = Typography;

const STATUS_COLORS: Record<string, string> = {
  draft: 'default', pending: 'orange', approved: 'blue', running: 'cyan',
  completed: 'green', failed: 'red', rolled_back: 'purple', cancelled: 'default', rejected: 'red',
};
const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', pending: '审批中', approved: '已审批', running: '发布中',
  completed: '已完成', failed: '失败', rolled_back: '已回滚', cancelled: '已取消', rejected: '已驳回',
};
const APPROVAL_STATUS_LABELS: Record<string, string> = {
  not_submitted: '未发起', submitting: '审批中', passed: '已通过',
  rejected: '已驳回', not_needed: '无需审批',
};
const APPROVAL_STATUS_COLORS: Record<string, string> = {
  not_submitted: 'default', submitting: 'processing', passed: 'success', rejected: 'error', not_needed: 'default',
};
const STRATEGY_LABELS: Record<string, string> = {
  rolling: '滚动更新', blue_green: '蓝绿部署', canary: '灰度发布',
};
const LOG_LEVEL_COLORS: Record<string, string> = {
  info: '#89b4fa', warn: '#f9e2af', error: '#f38ba8', debug: '#6c7086',
};

export default function ReleaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [release, setRelease] = useState<any>(null);
  const [ciLogs, setCiLogs] = useState<any[]>([]);
  const [cdLogs, setCdLogs] = useState<any[]>([]);
  const [verifications, setVerifications] = useState<any[]>([]);
  const [configReleases, setConfigReleases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const ciRef = useRef<HTMLDivElement>(null);
  const cdRef = useRef<HTMLDivElement>(null);

  const fetchVerifications = async () => {
    if (!id) return;
    try {
      const verRes = await releaseApi.verifications(Number(id));
      setVerifications(verRes?.data || []);
    } catch (e) {
      /* 忽略：验证板块加载失败不影响主流程 */
    }
  };

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [relRes, ciRes, cdRes, verRes, cfgRes] = await Promise.all([
        releaseApi.detail(Number(id)),
        releaseApi.ciLogs(Number(id)),
        releaseApi.cdLogs(Number(id)),
        releaseApi.verifications(Number(id)),
        configApi.releases.byRelease(Number(id)),
      ]);
      setRelease(relRes.data || relRes);
      setCiLogs(ciRes?.data || []);
      setCdLogs(cdRes?.data || []);
      setVerifications(verRes?.data || []);
      const cfgList = cfgRes?.data || [];
      // 并行拉取每个配置版本与上一次的 diff（配置随发布走 · 可追溯）
      Promise.all(cfgList.map((c: any) =>
        configApi.releases.diff(c.id)
          .then((d: any) => ({ ...c, diff: d?.data }))
          .catch(() => ({ ...c, diff: null })),
      )).then((list) => setConfigReleases(list));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  // 轮询：运行中时每 2s 刷新日志
  useEffect(() => {
    if (!release) return;
    const isRunning = release.status === 'running';
    if (!isRunning) return;
    const timer = setInterval(fetchData, 2000);
    return () => clearInterval(timer);
  }, [release?.status]);

  // 轮询：验证执行中时每 2s 刷新验证记录
  useEffect(() => {
    if (!verifications?.length) return;
    const hasRunning = verifications.some((v: any) => v.status === 'running');
    if (!hasRunning) return;
    const timer = setInterval(fetchVerifications, 2000);
    return () => clearInterval(timer);
  }, [verifications]);

  // 自动滚动到底部
  useEffect(() => {
    if (ciRef.current) ciRef.current.scrollTop = ciRef.current.scrollHeight;
  }, [ciLogs]);
  useEffect(() => {
    if (cdRef.current) cdRef.current.scrollTop = cdRef.current.scrollHeight;
  }, [cdLogs]);

  if (loading && !release) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spin size="large" /></div>;
  }
  if (!release) return <div>发布不存在</div>;

  const appName = release.application_name || release.application?.name || '-';
  const envName = release.environment_name || release.environment?.name || '-';
  const envCode = release.environment_code || release.environment?.code || '';
  const creatorName = release.creator_name || release.creator?.display_name || release.creator?.username || '-';
  const ciTask = (release.tasks || []).find((t: any) => t.stage === 'ci');
  const cdTask = (release.tasks || []).find((t: any) => t.stage === 'cd');
  const ciStatus = ciTask?.status || 'pending';
  const cdStatus = cdTask?.status || 'pending';
  const approvals = release.approvals || [];

  const canExecuteRelease = (!release.need_approval && release.status === 'draft')
    || release.approval_status === 'passed';

  const handleExecuteRelease = async () => {
    try {
      await releaseApi.execute(Number(id));
      message.success('发布已触发，CI 构建开始');
      fetchData();
    } catch (e: any) {
      message.error(e?.message || '触发发布失败');
    }
  };

  const handleRunVerify = async () => {
    try {
      await releaseApi.verify(Number(id));
      message.success('验证已触发，执行中...');
      fetchVerifications();
    } catch (e: any) {
      message.error(e?.message || '触发验证失败');
    }
  };

  const handleTriggerApproval = async () => {
    try {
      await releaseApi.submitApproval(Number(id));
      message.success('审批已提交');
      fetchData();
    } catch (e: any) {
      message.error(e?.message || '提交审批失败');
    }
  };

  const handleAutoApprove = async () => {
    try {
      await releaseApi.approveAction(Number(id), 'approved', 'Demo 自动审批通过');
      message.success('审批已通过');
      fetchData();
    } catch (e: any) {
      message.error(e?.message || '审批操作失败');
    }
  };

  const renderLogBody = (logs: any[], ref: React.RefObject<HTMLDivElement>) => (
    <div ref={ref} style={{
      background: '#1e1e2e', color: '#cdd6f4', padding: '12px 16px',
      minHeight: 200, maxHeight: '50vh', overflow: 'auto',
      fontFamily: "'SF Mono', Menlo, Consolas, monospace", fontSize: 12, lineHeight: 1.8,
      borderRadius: '0 0 8px 8px',
    }}>
      {logs.length === 0 && <div style={{ color: '#6c7086' }}>等待日志...</div>}
      {logs.map((l: any, i: number) => (
        <div key={i} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          <span style={{ color: '#6c7086' }}>[{l.created_at?.slice(11, 19) || ''}]</span>{' '}
          <span style={{ color: LOG_LEVEL_COLORS[l.level] || '#89b4fa' }}>
            [{(l.level || 'info').toUpperCase()}]
          </span>{' '}
          {l.message}
        </div>
      ))}
    </div>
  );

  const statusBadge = (s: string) => {
    const m: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '等待' },
      running: { color: 'processing', text: '🔄 执行中' },
      success: { color: 'success', text: '✅ 成功' },
      failed: { color: 'error', text: '❌ 失败' },
    };
    const cfg = m[s] || m.pending;
    return <Tag color={cfg.color} style={{ fontSize: 12 }}>{cfg.text}</Tag>;
  };

  const verificationStatusTag = (s: string) => {
    const m: Record<string, { color: string; text: string }> = {
      running: { color: 'processing', text: '🔄 执行中' },
      success: { color: 'success', text: '✅ 验证通过' },
      failed: { color: 'error', text: '❌ 验证失败' },
      skipped: { color: 'default', text: '⏭️ 已跳过' },
    };
    const cfg = m[s] || { color: 'default', text: s };
    return <Tag color={cfg.color} style={{ fontSize: 12 }}>{cfg.text}</Tag>;
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16, gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => {
          if (release?.application) {
            navigate(`/releases/app/${release.application}`);
          } else {
            navigate(-1);
          }
        }}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>发布详情</Title>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small">
          <Descriptions.Item label="发布单号"><Text code>{release.release_no}</Text></Descriptions.Item>
          <Descriptions.Item label="应用"><Text strong>{appName}</Text></Descriptions.Item>
          <Descriptions.Item label="环境">
            <Tag color={envCode === 'prod' ? 'red' : envCode === 'staging' ? 'orange' : envCode === 'test' ? 'green' : 'blue'}>{envName}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="版本">
            {release.release_mode === 'scale' ? <Text type="secondary">-</Text> : release.version}
          </Descriptions.Item>
          {release.release_mode === 'scale' && (
            <>
              <Descriptions.Item label="当前实例">{release.current_replicas ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="目标实例">
                <Tag color={release.target_replicas === 0 ? 'red' : 'blue'}>{release.target_replicas ?? '-'}</Tag>
              </Descriptions.Item>
            </>
          )}
          <Descriptions.Item label="状态"><Tag color={STATUS_COLORS[release.status]}>{STATUS_LABELS[release.status] || release.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="审批状态">
            <Tag color={APPROVAL_STATUS_COLORS[release.approval_status]}>
              {APPROVAL_STATUS_LABELS[release.approval_status] || release.approval_status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="策略">{STRATEGY_LABELS[release.deploy_strategy] || release.deploy_strategy}</Descriptions.Item>
          <Descriptions.Item label="创建人">{creatorName}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{release.created_at}</Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 12 }}>
          <Space>
            {release.status === 'draft' && release.need_approval && release.approval_status === 'not_submitted' && (
              <Button type="primary" onClick={handleTriggerApproval}>发起审批</Button>
            )}
            {release.approval_status === 'submitting' && (
              <Button type="primary" onClick={handleAutoApprove}>模拟审批通过</Button>
            )}
            {canExecuteRelease && release.status === 'draft' && (
              <Button type="primary" style={{ background: '#52c41a', borderColor: '#52c41a' }} onClick={handleExecuteRelease}>
                🚀 执行发布
              </Button>
            )}
          </Space>
        </div>
      </Card>

      {/* 审批链路 */}
      {release.need_approval && (
        <Card title="📋 审批链路" size="small" style={{ marginBottom: 16 }}>
          {approvals.length === 0 ? (
            <Text type="secondary">暂无审批记录</Text>
          ) : (
            <Timeline
              items={approvals.map((a: any) => ({
                color: a.action === 'approved' ? 'green' : a.action === 'rejected' ? 'red' : 'gray',
                dot: a.action === 'approved' ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  : a.action === 'rejected' ? <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                  : <ClockCircleOutlined style={{ color: '#999' }} />,
                children: (
                  <div>
                    <Text strong>{a.step_name || '步骤 1'}</Text>
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      审批人: {typeof a.approver === 'object' ? a.approver?.display_name || a.approver?.username : a.approver || '-'}
                    </Text>
                    <Tag color={a.action === 'approved' ? 'success' : a.action === 'rejected' ? 'error' : 'default'} style={{ marginLeft: 8 }}>
                      {a.action === 'approved' ? '通过' : a.action === 'rejected' ? '驳回' : '待审批'}
                    </Tag>
                    {a.comment && <div style={{ marginTop: 4 }}><Text type="secondary" style={{ fontSize: 12 }}>{a.comment}</Text></div>}
                    <div><Text type="secondary" style={{ fontSize: 12 }}>{a.created_at}</Text></div>
                  </div>
                ),
              }))}
            />
          )}
        </Card>
      )}

      {/* CI 构建面板 */}
      <Card
        title={<span>📦 CI 构建 {statusBadge(ciStatus)}</span>}
        style={{ marginBottom: 16 }}
        styles={{ body: { padding: 0 } }}
      >
        {renderLogBody(ciLogs, ciRef)}
      </Card>

      {/* CD 完成分隔线 */}
      {ciStatus === 'success' && (
        <div style={{
          textAlign: 'center', padding: '8px 0', fontSize: 12, fontWeight: 600,
          color: '#4f46e5', background: '#eef2ff', border: '1px dashed #c7d2fe',
          borderRadius: 8, margin: '4px 0 4px',
        }}>
          ── CI 完成，自动触发 CD ──
        </div>
      )}

      {/* CD 部署面板 */}
      <Card
        title={<span>🚀 CD 部署 {statusBadge(cdStatus)}</span>}
        styles={{ body: { padding: 0 } }}
      >
        {renderLogBody(cdLogs, cdRef)}
      </Card>

      {/* 本次配置（配置随发布走 · 可追溯可回滚） */}
      <Card
        title={<span>📄 本次配置</span>}
        size="small"
        style={{ marginTop: 16 }}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>发布 CD 时按 应用×环境 渲染并下发的配置版本</Text>}
      >
        {configReleases.length === 0 ? (
          <Text type="secondary">该发布未携带配置（应用未绑定配置模板）</Text>
        ) : (
          configReleases.map((cr: any) => (
            <div key={cr.id} style={{ marginBottom: 14 }}>
              <Space style={{ marginBottom: 6 }} wrap>
                <Text strong>{cr.template_name}</Text>
                <Tag color="blue">v{cr.version}</Tag>
                <Tag>{cr.environment_name}</Tag>
                <Tag color={cr.status === 'applied' ? 'green' : cr.status === 'rolled_back' ? 'purple' : 'default'}>
                  {cr.status === 'applied' ? '已应用' : cr.status === 'rolled_back' ? '已回滚' : '待应用'}
                </Tag>
              </Space>
              <pre style={{
                background: '#1e1e2e', color: '#cdd6f4', padding: '8px 12px',
                borderRadius: 6, fontSize: 12, lineHeight: 1.6, overflow: 'auto', whiteSpace: 'pre-wrap',
              }}>{cr.rendered_content}</pre>
              {cr.diff && cr.diff.diff && cr.diff.diff.length > 0 && (
                <div style={{ marginTop: 6 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    diff（{cr.diff.previous_version
                      ? `v${cr.diff.previous_version} → v${cr.diff.current_version}`
                      : '首次发布，全量新增'}）
                  </Text>
                  <pre style={{
                    background: '#f6f8fa', color: '#24292f', padding: '8px 12px',
                    borderRadius: 6, fontSize: 12, lineHeight: 1.6, overflow: 'auto', whiteSpace: 'pre-wrap',
                    border: '1px solid #d0d7de',
                  }}>
                    {cr.diff.diff.map((line: string, i: number) => {
                      const color = line.startsWith('+')
                        ? '#22863a' : line.startsWith('-')
                          ? '#cb2431' : '#6a737d';
                      return <div key={i} style={{ color }}>{line || ' '}</div>;
                    })}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
      </Card>

      {/* 发布验证板块 */}
      <Card
        title={<span>🔍 发布验证</span>}
        extra={
          <Space>
            <Button size="small" icon={<ReloadOutlined />} onClick={fetchVerifications}>刷新</Button>
            <Button size="small" type="primary" icon={<ThunderboltOutlined />} onClick={handleRunVerify}>运行验证</Button>
          </Space>
        }
        style={{ marginTop: 16 }}
      >
        {verifications.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px 0', color: '#6c7086' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
            <div>发布成功后自动验证，也可点击「运行验证」手动执行</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>检查项：部署状态 / 健康检查 / 版本验证（蓝绿查 selector、灰度查独立入口）</div>
          </div>
        ) : (
          verifications.map((v: any) => (
            <Card key={v.id} size="small" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
                <Space>
                  {verificationStatusTag(v.status)}
                  <Text type="secondary" style={{ fontSize: 12 }}>{v.created_at}</Text>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>{v.summary}</Text>
              </div>
              {(v.results || []).map((c: any, i: number) => (
                <div
                  key={i}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '5px 8px',
                    borderRadius: 6, marginBottom: 4,
                    background: c.status === 'pass' ? 'rgba(82,196,26,0.06)' : 'rgba(255,77,79,0.08)',
                  }}
                >
                  <span style={{ fontSize: 14 }}>{c.status === 'pass' ? '✅' : '❌'}</span>
                  <Text strong style={{ minWidth: 120, fontSize: 13 }}>{c.name}</Text>
                  <Text
                    style={{
                      flex: 1, fontSize: 12,
                      fontFamily: "'SF Mono', Menlo, Consolas, monospace",
                      color: c.status === 'pass' ? '#389e0d' : '#cf1322',
                      wordBreak: 'break-all',
                    }}
                  >
                    {c.evidence}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12, minWidth: 70, textAlign: 'right' }}>
                    {c.duration_ms}ms
                  </Text>
                </div>
              ))}
              {v.status === 'running' && (
                <div style={{ textAlign: 'center', padding: 8 }}>
                  <Spin size="small" /> <Text type="secondary" style={{ marginLeft: 8 }}>验证执行中...</Text>
                </div>
              )}
            </Card>
          ))
        )}
      </Card>
    </div>
  );
}