import { Typography, Divider } from 'antd';

const { Title, Paragraph, Text } = Typography;

export default function DocsArchitecture() {
  return (
    <div style={{ maxWidth: 800 }}>
      <Title>系统架构概览</Title>

      <Divider />

      <Title level={2}>前端架构</Title>
      <Paragraph>
        <Text strong>技术栈：</Text>
        <code>React 18</code> + <code>TypeScript</code> + <code>Ant Design 5</code> + <code>Zustand</code>
      </Paragraph>
      <Paragraph>
        前端采用 <Text strong>SPA（单页应用）</Text>架构，使用 React Router 实现客户端路由。
        全局状态管理使用 Zustand，负责用户认证信息、权限等跨页面共享状态的管理。
        UI 组件库使用 Ant Design 5，提供丰富的企业级组件支持。
      </Paragraph>
      <Paragraph>
        API 请求统一封装在 <code>src/api</code> 目录下，通过 axios 实例与后端通信，
        自动处理 JWT Token 的携带与刷新。
      </Paragraph>

      <Divider />

      <Title level={2}>后端架构</Title>
      <Paragraph>
        <Text strong>技术栈：</Text>
        <code>Django 4.2</code> + <code>Django REST Framework</code> + <code>SimpleJWT</code> + <code>SQLite</code>
      </Paragraph>
      <Paragraph>
        后端采用 <Text strong>Django REST Framework</Text> 构建 RESTful API，使用
        <code>django-simplejwt</code> 实现基于 JWT 的用户认证。
        权限控制通过 <Text strong>Django REST Framework 的权限系统</Text> + 自定义的 RBAC 实现。
      </Paragraph>
      <Paragraph>
        数据库使用 <Text strong>SQLite</Text>，便于本地开发和 Demo 演示。
        应用部署采用 <Text strong>Gunicorn</Text> + <Text strong>Nginx</Text> 的生产级架构。
      </Paragraph>

      <Divider />

      <Title level={2}>部署架构</Title>
      <Paragraph>
        <Text strong>运行环境：</Text>
        <code>K8s</code>（<code>kind</code> 本地集群）
      </Paragraph>
      <Paragraph>
        整个系统在 <Text strong>kind（Kubernetes in Docker）</Text>集群中运行。
        前端通过 Nginx 容器提供静态文件服务，后端通过 Gunicorn + Nginx 容器提供 API 服务。
        使用 <code>kubectl</code> 管理部署和滚动更新。
      </Paragraph>

      <Divider />

      <Title level={2}>数据流</Title>
      <Paragraph>
        系统核心数据流如下：
      </Paragraph>
      <Paragraph>
        <Text code>用户操作 → API 请求 → 权限校验 → 业务逻辑处理 → 数据库读写 → 响应返回</Text>
      </Paragraph>
      <Paragraph>
        <ul>
          <li>
            <Text strong>用户操作：</Text>用户在浏览器中进行操作（创建发布单、审批、查看制品等）
          </li>
          <li>
            <Text strong>API 请求：</Text>前端通过 axios 发送 HTTP 请求到后端 REST API
          </li>
          <li>
            <Text strong>权限校验：</Text>后端通过 JWT 中间件解析用户身份，DRF 权限类校验操作权限
          </li>
          <li>
            <Text strong>业务逻辑：</Text>ViewSet / APIView 中执行业务逻辑（创建发布单、触发流水线等）
          </li>
          <li>
            <Text strong>数据库：</Text>通过 Django ORM 进行数据库读写操作
          </li>
          <li>
            <Text strong>响应返回：</Text>序列化后的数据通过 JSON 响应返回给前端
          </li>
        </ul>
      </Paragraph>
    </div>
  );
}