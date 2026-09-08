import { Card, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  CloudServerOutlined,
  SafetyCertificateOutlined,
  DeploymentUnitOutlined,
  ApartmentOutlined,
  DockerOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';

const { Title } = Typography;

const docCards = [
  {
    title: '系统架构',
    description: '整体架构设计',
    icon: <CloudServerOutlined style={{ fontSize: 32, color: '#1677ff' }} />,
    path: '/docs/architecture',
  },
  {
    title: '权限模型',
    description: '组织树 + RBAC 设计',
    icon: <SafetyCertificateOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
    path: '/docs/architecture',
  },
  {
    title: '发布流水线',
    description: '发布流程与阶段说明',
    icon: <DeploymentUnitOutlined style={{ fontSize: 32, color: '#faad14' }} />,
    path: '/docs/architecture',
  },
  {
    title: '部署模式',
    description: 'EC2 vs K8s 双路径',
    icon: <ApartmentOutlined style={{ fontSize: 32, color: '#ff4d4f' }} />,
    path: '/docs/architecture',
  },
  {
    title: '双镜像设计',
    description: 'CI 构建策略',
    icon: <DockerOutlined style={{ fontSize: 32, color: '#1677ff' }} />,
    path: '/docs/architecture',
  },
  {
    title: '面试指南',
    description: '常见面试题与回答思路',
    icon: <QuestionCircleOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
    path: '/docs/interview',
  },
];

export default function DocsPage() {
  const navigate = useNavigate();

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>面试文档</Title>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {docCards.map((card) => (
          <Card
            key={card.title}
            hoverable
            onClick={() => navigate(card.path)}
            style={{ borderRadius: 8 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              {card.icon}
              <div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>{card.title}</div>
                <div style={{ color: '#888', fontSize: 13, marginTop: 4 }}>{card.description}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}