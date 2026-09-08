// 1. 发布流水线流程图
export function ReleasePipelineDiagram() {
  return (
    <svg viewBox="0 0 800 200" style={{ width: '100%', maxWidth: 800 }}>
      {/* 11 stages in a horizontal flow with arrows */}
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
        </marker>
      </defs>
      {/* Row 1: 构建 → 部署开发 → 验证开发 → 部署测试 → 验证测试 */}
      {[
        { x: 20, label: '构建', color: '#1890ff' },
        { x: 130, label: '部署开发', color: '#52c41a' },
        { x: 240, label: '验证开发', color: '#faad14' },
        { x: 350, label: '部署测试', color: '#52c41a' },
        { x: 460, label: '验证测试', color: '#faad14' },
      ].map((item, i) => (
        <g key={i}>
          <rect x={item.x} y={20} width={80} height={36} rx={18} fill={item.color} opacity={0.9} />
          <text x={item.x + 40} y={42} textAnchor="middle" fill="white" fontSize={12} fontWeight="bold">{item.label}</text>
          {i < 4 && <line x1={item.x + 80} y1={38} x2={item.x + 110} y2={38} stroke="#666" strokeWidth={2} markerEnd="url(#arrow)" />}
        </g>
      ))}
      {/* Row 2: 预发审批 → 部署预发 → 验证预发 → 灰度发布 → 全量发布 → 最终验证 */}
      {[
        { x: 60, label: '预发审批', color: '#722ed1' },
        { x: 170, label: '部署预发', color: '#52c41a' },
        { x: 280, label: '验证预发', color: '#faad14' },
        { x: 390, label: '灰度发布', color: '#eb2f96' },
        { x: 500, label: '全量发布', color: '#f5222d' },
        { x: 610, label: '最终验证', color: '#13c2c2' },
      ].map((item, i) => (
        <g key={i + 5}>
          <rect x={item.x} y={80} width={80} height={36} rx={18} fill={item.color} opacity={0.9} />
          <text x={item.x + 40} y={102} textAnchor="middle" fill="white" fontSize={12} fontWeight="bold">{item.label}</text>
          {i < 5 && <line x1={item.x + 80} y1={98} x2={item.x + 110} y2={98} stroke="#666" strokeWidth={2} markerEnd="url(#arrow)" />}
        </g>
      ))}
      {/* Arrow from row 1 to row 2 */}
      <path d="M 500 56 L 500 70 L 140 70 L 140 80" stroke="#666" strokeWidth={2} fill="none" markerEnd="url(#arrow)" />
      <text x={250} y={68} textAnchor="middle" fill="#666" fontSize={11}>阶段通过后自动进入下一行</text>
    </svg>
  );
}

// 2. 系统架构图
export function SystemArchitectureDiagram() {
  return (
    <svg viewBox="0 0 800 500" style={{ width: '100%', maxWidth: 800 }}>
      <defs>
        <marker id="arrow2" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
        </marker>
      </defs>
      {/* 标题层 */}
      <rect x={250} y={10} width={300} height={40} rx={6} fill="#1890ff" />
      <text x={400} y={35} textAnchor="middle" fill="white" fontSize={16} fontWeight="bold">Release System Demo - 系统架构</text>

      {/* 前端层 */}
      <rect x={50} y={80} width={200} height={140} rx={8} fill="#e6f7ff" stroke="#1890ff" strokeWidth={2} />
      <text x={150} y={105} textAnchor="middle" fill="#1890ff" fontSize={14} fontWeight="bold">前端 (React + Vite)</text>
      <text x={150} y={130} textAnchor="middle" fill="#333" fontSize={11}>Ant Design 组件库</text>
      <text x={150} y={150} textAnchor="middle" fill="#333" fontSize={11}>Zustand 状态管理</text>
      <text x={150} y={170} textAnchor="middle" fill="#333" fontSize={11}>React Router 路由</text>
      <text x={150} y={190} textAnchor="middle" fill="#333" fontSize={11}>TypeScript 类型安全</text>

      {/* API 网关层 */}
      <rect x={300} y={100} width={200} height={60} rx={8} fill="#fff7e6" stroke="#fa8c16" strokeWidth={2} />
      <text x={400} y={125} textAnchor="middle" fill="#fa8c16" fontSize={14} fontWeight="bold">API 网关 (Django REST)</text>
      <text x={400} y={148} textAnchor="middle" fill="#333" fontSize={11}>JWT 认证 / 权限校验</text>

      {/* 后端层 */}
      <rect x={550} y={80} width={200} height={140} rx={8} fill="#f6ffed" stroke="#52c41a" strokeWidth={2} />
      <text x={650} y={105} textAnchor="middle" fill="#52c41a" fontSize={14} fontWeight="bold">后端 (Django 4.2)</text>
      <text x={650} y={130} textAnchor="middle" fill="#333" fontSize={11}>11 个业务模块</text>
      <text x={650} y={150} textAnchor="middle" fill="#333" fontSize={11}>FBV 视图模式</text>
      <text x={650} y={170} textAnchor="middle" fill="#333" fontSize={11}>SQLite 数据库</text>
      <text x={650} y={190} textAnchor="middle" fill="#333" fontSize={11}>20 张数据表</text>

      {/* 箭头: 前端 → API */}
      <line x1={250} y1={130} x2={300} y2={130} stroke="#666" strokeWidth={2} markerEnd="url(#arrow2)" />
      {/* 箭头: API → 后端 */}
      <line x1={500} y1={130} x2={550} y2={130} stroke="#666" strokeWidth={2} markerEnd="url(#arrow2)" />

      {/* 基础设施层 */}
      <rect x={100} y={260} width={600} height={90} rx={8} fill="#f9f0ff" stroke="#722ed1" strokeWidth={2} />
      <text x={400} y={285} textAnchor="middle" fill="#722ed1" fontSize={14} fontWeight="bold">基础设施</text>
      <text x={200} y={315} textAnchor="middle" fill="#333" fontSize={11}>Kind 集群 (本地 K8s)</text>
      <text x={400} y={315} textAnchor="middle" fill="#333" fontSize={11}>3 个 Demo 应用 (Python/Go/Node)</text>
      <text x={600} y={315} textAnchor="middle" fill="#333" fontSize={11}>Deployment / Service / ConfigMap</text>

      {/* 箭头: 后端 → 基础设施 */}
      <line x1={400} y1={220} x2={400} y2={260} stroke="#666" strokeWidth={2} markerEnd="url(#arrow2)" />

      {/* 数据流标注 */}
      <rect x={250} y={380} width={300} height={60} rx={6} fill="#fff0f6" stroke="#eb2f96" strokeWidth={1.5} />
      <text x={400} y={405} textAnchor="middle" fill="#eb2f96" fontSize={13} fontWeight="bold">数据流</text>
      <text x={400} y={425} textAnchor="middle" fill="#333" fontSize={11}>用户操作 → API 请求 → 权限校验 → 业务逻辑 → 数据库</text>
    </svg>
  );
}

// 3. 双镜像 CI/CD 流程图
export function DualImageDiagram() {
  return (
    <svg viewBox="0 0 800 320" style={{ width: '100%', maxWidth: 800 }}>
      <defs>
        <marker id="arrow3" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
        </marker>
      </defs>

      {/* 基础镜像 */}
      <rect x={30} y={20} width={160} height={50} rx={6} fill="#e6f7ff" stroke="#1890ff" strokeWidth={2} />
      <text x={110} y={40} textAnchor="middle" fill="#1890ff" fontSize={12} fontWeight="bold">环境基础镜像</text>
      <text x={110} y={58} textAnchor="middle" fill="#666" fontSize={10}>golang:1.23-alpine</text>

      <rect x={30} y={90} width={160} height={50} rx={6} fill="#f6ffed" stroke="#52c41a" strokeWidth={2} />
      <text x={110} y={110} textAnchor="middle" fill="#52c41a" fontSize={12} fontWeight="bold">应用基础镜像</text>
      <text x={110} y={128} textAnchor="middle" fill="#666" fontSize={10}>alpine:3.20</text>

      {/* CI 阶段 */}
      <rect x={260} y={20} width={180} height={120} rx={8} fill="#fff7e6" stroke="#fa8c16" strokeWidth={2} />
      <text x={350} y={45} textAnchor="middle" fill="#fa8c16" fontSize={14} fontWeight="bold">CI 构建阶段</text>
      <text x={350} y={70} textAnchor="middle" fill="#333" fontSize={11}>1. 拉取环境基础镜像</text>
      <text x={350} y={90} textAnchor="middle" fill="#333" fontSize={11}>2. 编译代码生成产物</text>
      <text x={350} y={110} textAnchor="middle" fill="#333" fontSize={11}>3. 产物拷贝到应用基础镜像</text>
      <text x={350} y={130} textAnchor="middle" fill="#333" fontSize={11}>4. 推送最终镜像到仓库</text>

      {/* 最终镜像 */}
      <rect x={510} y={40} width={160} height={50} rx={6} fill="#fff0f6" stroke="#eb2f96" strokeWidth={2} />
      <text x={590} y={60} textAnchor="middle" fill="#eb2f96" fontSize={12} fontWeight="bold">最终运行镜像</text>
      <text x={590} y={78} textAnchor="middle" fill="#666" fontSize={10}>体积小 / 启动快 / 安全</text>

      {/* CD 部署 */}
      <rect x={510} y={120} width={160} height={50} rx={6} fill="#f9f0ff" stroke="#722ed1" strokeWidth={2} />
      <text x={590} y={140} textAnchor="middle" fill="#722ed1" fontSize={12} fontWeight="bold">CD 部署阶段</text>
      <text x={590} y={158} textAnchor="middle" fill="#666" fontSize={10}>kubectl set image</text>

      {/* 箭头 */}
      <line x1={190} y1={45} x2={260} y2={45} stroke="#666" strokeWidth={2} markerEnd="url(#arrow3)" />
      <line x1={190} y1={115} x2={260} y2={115} stroke="#666" strokeWidth={2} markerEnd="url(#arrow3)" />
      <line x1={440} y1={65} x2={510} y2={65} stroke="#666" strokeWidth={2} markerEnd="url(#arrow3)" />
      <line x1={590} y1={90} x2={590} y2={120} stroke="#666" strokeWidth={2} markerEnd="url(#arrow3)" />

      {/* 标注 */}
      <text x={350} y={170} textAnchor="middle" fill="#999" fontSize={10}>环境基础镜像: 仅用于编译，用完即销毁</text>
      <text x={350} y={185} textAnchor="middle" fill="#999" fontSize={10}>应用基础镜像: 预装运行环境，只包含产物</text>
    </svg>
  );
}

// 4. 权限模型图
export function PermissionModelDiagram() {
  return (
    <svg viewBox="0 0 800 350" style={{ width: '100%', maxWidth: 800 }}>
      <defs>
        <marker id="arrow4" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
        </marker>
      </defs>

      {/* 组织树侧 */}
      <rect x={20} y={10} width={220} height={200} rx={8} fill="#e6f7ff" stroke="#1890ff" strokeWidth={2} />
      <text x={130} y={35} textAnchor="middle" fill="#1890ff" fontSize={14} fontWeight="bold">组织树</text>
      <text x={40} y={60} fill="#333" fontSize={11}> 业务线 (BusinessLine)</text>
      <text x={55} y={80} fill="#333" fontSize={11}>├── 组 (Group)</text>
      <text x={70} y={100} fill="#333" fontSize={11}>│   ├── 成员 (归属)</text>
      <text x={70} y={120} fill="#333" fontSize={11}>│   ├── 成员 (协作)</text>
      <text x={55} y={140} fill="#333" fontSize={11}>├── 组 (Group)</text>
      <text x={70} y={160} fill="#333" fontSize={11}>│   └── 成员</text>
      <text x={40} y={185} fill="#999" fontSize={10}>用于快速定位人员和权限</text>

      {/* 角色侧 */}
      <rect x={290} y={10} width={220} height={200} rx={8} fill="#fff7e6" stroke="#fa8c16" strokeWidth={2} />
      <text x={400} y={35} textAnchor="middle" fill="#fa8c16" fontSize={14} fontWeight="bold">RBAC 角色</text>
      <text x={310} y={60} fill="#333" fontSize={11}> 管理员 (admin)</text>
      <text x={310} y={80} fill="#333" fontSize={11}> 应用负责人 (app_owner)</text>
      <text x={310} y={100} fill="#333" fontSize={11}> 开发者 (developer)</text>
      <text x={310} y={120} fill="#333" fontSize={11}> 运维 (operator)</text>
      <text x={310} y={140} fill="#333" fontSize={11}> 审批人 (approver)</text>
      <text x={310} y={160} fill="#333" fontSize={11}> 普通用户 (normal)</text>
      <text x={310} y={185} fill="#999" fontSize={10}>每个角色关联一组权限码</text>

      {/* 权限侧 */}
      <rect x={560} y={10} width={220} height={200} rx={8} fill="#f6ffed" stroke="#52c41a" strokeWidth={2} />
      <text x={670} y={35} textAnchor="middle" fill="#52c41a" fontSize={14} fontWeight="bold">权限分配</text>
      <text x={580} y={60} fill="#333" fontSize={11}> 组权限 (GroupPermission)</text>
      <text x={580} y={80} fill="#333" fontSize={11}>  ├─ 角色 + 资源范围</text>
      <text x={580} y={100} fill="#333" fontSize={11}>  ├─ 业务线/应用/环境</text>
      <text x={580} y={120} fill="#333" fontSize={11}> 个人例外 (UserPermission)</text>
      <text x={580} y={140} fill="#333" fontSize={11}>  ├─ 允许/拒绝覆盖</text>
      <text x={580} y={160} fill="#333" fontSize={11}>  └─ 可设置有效期</text>
      <text x={580} y={185} fill="#999" fontSize={10}>个人权限 &lt; 组权限 (继承)</text>

      {/* 箭头 */}
      <line x1={240} y1={100} x2={290} y2={70} stroke="#666" strokeWidth={2} markerEnd="url(#arrow4)" />
      <line x1={510} y1={100} x2={560} y2={100} stroke="#666" strokeWidth={2} markerEnd="url(#arrow4)" />
      <text x={265} y={85} textAnchor="middle" fill="#666" fontSize={10}>绑定</text>
      <text x={535} y={115} textAnchor="middle" fill="#666" fontSize={10}>授权</text>

      {/* 最下方 */}
      <rect x={200} y={240} width={400} height={50} rx={6} fill="#f9f0ff" stroke="#722ed1" strokeWidth={1.5} />
      <text x={400} y={260} textAnchor="middle" fill="#722ed1" fontSize={12} fontWeight="bold">权限校验逻辑</text>
      <text x={400} y={278} textAnchor="middle" fill="#333" fontSize={11}>个人 DENY → 个人 ALLOW → 组 ALLOW → 默认拒绝</text>
    </svg>
  );
}