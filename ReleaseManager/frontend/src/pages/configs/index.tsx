import { Card, Row, Col, Typography } from 'antd';
import { SettingOutlined, FileTextOutlined, HistoryOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

export default function ConfigIndexPage() {
  const navigate = useNavigate();

  const cards = [
    {
      title: '配置模板',
      description: '管理配置模板，支持 YAML、Properties、ENV、JSON、Nginx 等多种格式',
      icon: <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      path: '/config/templates',
    },
    {
      title: '变量管理',
      description: '管理配置模板中的变量，按环境设置不同的变量值',
      icon: <SettingOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      path: '/config/variables',
    },
    {
      title: '配置发布记录',
      description: '查看配置发布历史，比较不同版本间的配置差异',
      icon: <HistoryOutlined style={{ fontSize: 48, color: '#faad14' }} />,
      path: '/config/releases',
    },
  ];

  return (
    <div>
      <Title level={4}>配置管理</Title>
      <Row gutter={[24, 24]} style={{ marginTop: 16 }}>
        {cards.map((card) => (
          <Col span={8} key={card.path}>
            <Card
              hoverable
              onClick={() => navigate(card.path)}
              style={{ height: '100%' }}
            >
              <div style={{ textAlign: 'center', padding: '24px 0' }}>
                {card.icon}
                <Title level={4} style={{ marginTop: 16 }}>{card.title}</Title>
                <p style={{ color: '#666' }}>{card.description}</p>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}