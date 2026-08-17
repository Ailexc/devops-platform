"""
DemoStore — 开发环境的内存数据存储与种子数据。

Phase 1 阶段后端没有真实数据库模型，API 视图原先直接返回硬编码 stub。
为了演示"前后端真实联调"，这里提供一个模块级单例存储：

  1. 首次访问时自动播种演示数据 (ensure_seeded)
  2. 提供与管理命令 `seed_demo_data` 配合的显式重播种入口
  3. API 视图从这里读取数据，而不是在视图里写死

后续接入真实数据库时，只需将本模块替换为 ORM 查询即可，视图层无需改动。
"""

from __future__ import annotations

import threading

# ════════════════════════════════════════════════════════════════════
# 演示数据定义
# ════════════════════════════════════════════════════════════════════

DEMO_STATS = {
    "today_tasks": 342,
    "success_rate_24h": "98.7%",
    "aws_sync_today": 186,
    "internal_sync_today": 94,
    "inspection_today": 62,
    "pending_errors": 7,
    "total_cmdb_resources": "2.4M",
    "avg_duration": "28s",
}

# ── 监控大盘增强数据 ──────────────────────────────────────────────

# 24 小时任务执行趋势（每小时的任务数）
DEMO_TASK_TREND = [
    {"hour": "00", "success": 5, "failed": 0, "total": 5},
    {"hour": "01", "success": 3, "failed": 0, "total": 3},
    {"hour": "02", "success": 18, "failed": 1, "total": 19},
    {"hour": "03", "success": 42, "failed": 2, "total": 44},
    {"hour": "04", "success": 38, "failed": 1, "total": 39},
    {"hour": "05", "success": 35, "failed": 0, "total": 35},
    {"hour": "06", "success": 28, "failed": 1, "total": 29},
    {"hour": "07", "success": 22, "failed": 0, "total": 22},
    {"hour": "08", "success": 15, "failed": 0, "total": 15},
    {"hour": "09", "success": 8, "failed": 0, "total": 8},
    {"hour": "10", "success": 5, "failed": 0, "total": 5},
    {"hour": "11", "success": 3, "failed": 0, "total": 3},
    {"hour": "12", "success": 2, "failed": 0, "total": 2},
    {"hour": "13", "success": 6, "failed": 0, "total": 6},
    {"hour": "14", "success": 12, "failed": 1, "total": 13},
    {"hour": "15", "success": 25, "failed": 1, "total": 26},
    {"hour": "16", "success": 18, "failed": 0, "total": 18},
    {"hour": "17", "success": 10, "failed": 0, "total": 10},
    {"hour": "18", "success": 6, "failed": 0, "total": 6},
    {"hour": "19", "success": 4, "failed": 0, "total": 4},
    {"hour": "20", "success": 3, "failed": 0, "total": 3},
    {"hour": "21", "success": 3, "failed": 0, "total": 3},
    {"hour": "22", "success": 4, "failed": 0, "total": 4},
    {"hour": "23", "success": 5, "failed": 0, "total": 5},
]

# 最近告警/事件
DEMO_RECENT_EVENTS = [
    {"time": "15:35", "level": "error", "source": "AWS IAM", "message": "AssumeRole 凭据过期，IAM 同步失败", "task_id": "#10338"},
    {"time": "15:29", "level": "warning", "source": "AWS EC2", "message": "生产-apse1 同步正在运行中，已耗时 6m+", "task_id": "#10339"},
    {"time": "15:26", "level": "success", "source": "AWS EC2", "message": "生产-apne1 全量同步完成 (2m34s)", "task_id": "#10342"},
    {"time": "15:22", "level": "success", "source": "内部 Jira", "message": "Jira 工单增量同步完成 (1m05s)", "task_id": "#10330"},
    {"time": "15:20", "level": "error", "source": "AWS IAM", "message": "生产-IAM 增量同步失败: 凭据过期", "task_id": "#10338"},
    {"time": "15:15", "level": "success", "source": "内部 Jenkins", "message": "Jenkins 构建同步完成 (8s)", "task_id": "#10329"},
]

# 各资源类型同步统计
DEMO_RESOURCE_BREAKDOWN = [
    {"name": "EC2 实例", "count": 1245, "icon": "🖥️", "trend": "+12"},
    {"name": "RDS 数据库", "count": 86, "icon": "🗄️", "trend": "+2"},
    {"name": "VPC 网络", "count": 45, "icon": "🌐", "trend": "0"},
    {"name": "ELB 负载均衡", "count": 32, "icon": "⚖️", "trend": "+1"},
    {"name": "IAM 用户/角色", "count": 312, "icon": "🔐", "trend": "+5"},
    {"name": "安全组", "count": 1250, "icon": "🛡️", "trend": "+2"},
]

# ── AWS 资源管理数据 ──────────────────────────────────────────────

DEMO_AWS_RESOURCES = {
    "accounts": [
        {
            "name": "生产环境",
            "icon": "🏭",
            "account_id": "123456789012",
            "coverage": "4/4",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "resource_groups": [
                        {"name": "计算", "icon": "🖥️", "resources": ["EC2", "网卡"]},
                        {"name": "安全", "icon": "🛡️", "resources": ["安全组", "IAM"]},
                        {"name": "数据库", "icon": "🗄️", "resources": ["RDS", "快照"]},
                        {"name": "网络", "icon": "🌐", "resources": ["VPC", "子网", "ELB"]},
                        {"name": "存储", "icon": "💾", "resources": ["EBS", "S3"]},
                    ],
                    "relationships": [
                        {"source": "EC2", "source_icon": "🖥️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "实例所属 VPC"},
                        {"source": "EC2", "source_icon": "🖥️", "target": "子网", "target_icon": "🔗", "cardinality": "n:1", "key": "SubnetId", "desc": "实例所在子网"},
                        {"source": "EC2", "source_icon": "🖥️", "target": "安全组", "target_icon": "🛡️", "cardinality": "n:n", "key": "SecurityGroupIds", "desc": "实例绑定的安全组"},
                        {"source": "EC2", "source_icon": "🖥️", "target": "EBS", "target_icon": "💾", "cardinality": "1:n", "key": "BlockDeviceMappings", "desc": "实例挂载的磁盘"},
                        {"source": "RDS", "source_icon": "🗄️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "DBSubnetGroup", "desc": "数据库所属 VPC"},
                        {"source": "RDS", "source_icon": "🗄️", "target": "安全组", "target_icon": "🛡️", "cardinality": "n:n", "key": "VpcSecurityGroupIds", "desc": "数据库绑定的安全组"},
                        {"source": "ELB", "source_icon": "⚖️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "负载均衡所属 VPC"},
                        {"source": "ELB", "source_icon": "⚖️", "target": "子网", "target_icon": "🔗", "cardinality": "n:n", "key": "AvailabilityZones", "desc": "负载均衡分布的子网"},
                        {"source": "ELB", "source_icon": "⚖️", "target": "EC2", "target_icon": "🖥️", "cardinality": "n:n", "key": "TargetGroup", "desc": "后端实例目标组"},
                        {"source": "安全组", "source_icon": "🛡️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "安全组所属 VPC"},
                    ],
                },
                {
                    "code": "us-east-1",
                    "resource_groups": [
                        {"name": "计算", "icon": "🖥️", "resources": ["EC2", "网卡"]},
                        {"name": "安全", "icon": "🛡️", "resources": ["安全组", "IAM"]},
                        {"name": "数据库", "icon": "🗄️", "resources": ["RDS"]},
                        {"name": "网络", "icon": "🌐", "resources": ["VPC", "ELB"]},
                        {"name": "存储", "icon": "💾", "resources": ["EBS"]},
                    ],
                    "relationships": [
                        {"source": "EC2", "source_icon": "🖥️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "实例所属 VPC"},
                        {"source": "EC2", "source_icon": "🖥️", "target": "安全组", "target_icon": "🛡️", "cardinality": "n:n", "key": "SecurityGroupIds", "desc": "实例绑定的安全组"},
                        {"source": "RDS", "source_icon": "🗄️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "DBSubnetGroup", "desc": "数据库所属 VPC"},
                    ],
                },
                {
                    "code": "eu-west-1",
                    "resource_groups": [
                        {"name": "计算", "icon": "🖥️", "resources": ["EC2"]},
                        {"name": "网络", "icon": "🌐", "resources": ["VPC", "ELB"]},
                        {"name": "存储", "icon": "💾", "resources": ["EBS"]},
                    ],
                    "relationships": [
                        {"source": "EC2", "source_icon": "🖥️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "实例所属 VPC"},
                    ],
                },
                {
                    "code": "ap-southeast-1",
                    "resource_groups": [],
                    "relationships": [],
                },
            ],
        },
        {
            "name": "预发布环境",
            "icon": "🧪",
            "account_id": "987654321098",
            "coverage": "2/3",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "resource_groups": [
                        {"name": "计算", "icon": "🖥️", "resources": ["EC2"]},
                        {"name": "安全", "icon": "🛡️", "resources": ["安全组"]},
                        {"name": "数据库", "icon": "🗄️", "resources": ["RDS"]},
                        {"name": "网络", "icon": "🌐", "resources": ["VPC", "ELB"]},
                        {"name": "存储", "icon": "💾", "resources": ["EBS"]},
                    ],
                    "relationships": [
                        {"source": "EC2", "source_icon": "🖥️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "实例所属 VPC"},
                        {"source": "EC2", "source_icon": "🖥️", "target": "安全组", "target_icon": "🛡️", "cardinality": "n:n", "key": "SecurityGroupIds", "desc": "实例绑定的安全组"},
                        {"source": "RDS", "source_icon": "🗄️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "DBSubnetGroup", "desc": "数据库所属 VPC"},
                    ],
                },
                {
                    "code": "us-east-1",
                    "resource_groups": [],
                    "relationships": [],
                },
                {
                    "code": "eu-west-1",
                    "resource_groups": [],
                    "relationships": [],
                },
            ],
        },
        {
            "name": "开发环境",
            "icon": "💻",
            "account_id": "555666777888",
            "coverage": "1/2",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "resource_groups": [
                        {"name": "计算", "icon": "🖥️", "resources": ["EC2"]},
                        {"name": "安全", "icon": "🛡️", "resources": ["安全组"]},
                        {"name": "网络", "icon": "🌐", "resources": ["VPC"]},
                        {"name": "存储", "icon": "💾", "resources": ["EBS"]},
                    ],
                    "relationships": [
                        {"source": "EC2", "source_icon": "🖥️", "target": "VPC", "target_icon": "🌐", "cardinality": "n:1", "key": "VpcId", "desc": "实例所属 VPC"},
                    ],
                },
                {
                    "code": "us-east-1",
                    "resource_groups": [],
                    "relationships": [],
                },
            ],
        },
    ],
}

DEMO_WORKERS = [
    {"name": "worker-aws", "tasks": 186, "uptime": "6h12m", "status": "online"},
    {"name": "worker-connector", "tasks": 94, "uptime": "6h12m", "status": "online"},
    {"name": "worker-inspection", "tasks": 62, "uptime": "6h12m", "status": "online"},
]
DEMO_LOAD = "52%"

DEMO_HEALTH = [
    {"name": "AWS", "rate": "99.1%", "failed": 12, "total": 186},
    {"name": "内部系统", "rate": "97.9%", "failed": 2, "total": 94},
    {"name": "巡检", "rate": "95.2%", "failed": 3, "total": 62},
]

DEMO_FRESHNESS = {
    "AWS": "2m",
    "Lark": "12m",
    "Jira": "8m",
    "钉钉": "3m",
    "巡检": "22h",
}

DEMO_TASK_TREE = {
    "accounts": [
        {
            "name": "生产环境",
            "account_id": "123456789012",
            "coverage": "4/4",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "status": "synced",
                    "last_sync": "15:26-15:28",
                    "duration": "2m34s",
                    "cron": "0 2 * * *",
                    "concurrency": 50,
                    "resource_groups": [
                        {
                            "name": "计算",
                            "status": "success",
                            "resources": [
                                {"name": "EC2", "added": 5, "updated": 3, "deleted": 1},
                                {"name": "安全组", "added": 2, "updated": 0, "deleted": 0},
                                {"name": "网卡", "added": 0, "updated": 0, "deleted": 0},
                            ],
                        },
                        {
                            "name": "安全",
                            "status": "failed",
                            "resources": [
                                {"name": "IAM", "added": 0, "updated": 0, "deleted": 0, "error": "AssumeRole过期"},
                            ],
                        },
                        {
                            "name": "数据库",
                            "status": "success",
                            "resources": [
                                {"name": "RDS", "added": 2, "updated": 1, "deleted": 0},
                                {"name": "快照", "added": 3, "updated": 0, "deleted": 0},
                            ],
                        },
                        {
                            "name": "网络",
                            "status": "success",
                            "resources": [
                                {"name": "VPC", "added": 0, "updated": 0, "deleted": 0},
                                {"name": "ELB", "added": 1, "updated": 0, "deleted": 0},
                            ],
                        },
                    ],
                },
                {
                    "code": "us-east-1",
                    "status": "synced",
                    "last_sync": "14:55-14:58",
                    "duration": "2m47s",
                    "cron": "0 3 * * *",
                    "concurrency": 50,
                    "resource_groups": [
                        {
                            "name": "计算",
                            "status": "success",
                            "resources": [
                                {"name": "EC2", "added": 2, "updated": 1, "deleted": 0},
                            ],
                        },
                    ],
                },
                {
                    "code": "eu-west-1",
                    "status": "synced",
                    "last_sync": "05:00-05:03",
                    "duration": "3m12s",
                    "cron": "0 5 * * *",
                    "concurrency": 30,
                    "resource_groups": [],
                },
                {
                    "code": "ap-southeast-1",
                    "status": "syncing",
                    "last_sync": "-",
                    "duration": "-",
                    "cron": "0 4 * * *",
                    "concurrency": 30,
                    "resource_groups": [],
                },
            ],
        },
        {
            "name": "预发布环境",
            "account_id": "987654321098",
            "coverage": "2/3",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "status": "synced",
                    "last_sync": "03:00-03:02",
                    "duration": "2m01s",
                    "cron": "0 3 * * *",
                    "concurrency": 20,
                    "resource_groups": [
                        {
                            "name": "计算",
                            "status": "success",
                            "resources": [
                                {"name": "EC2", "added": 1, "updated": 0, "deleted": 0},
                            ],
                        },
                    ],
                },
                {
                    "code": "us-east-1",
                    "status": "syncing",
                    "last_sync": "-",
                    "duration": "-",
                    "cron": "0 4 * * *",
                    "concurrency": 20,
                    "resource_groups": [],
                },
                {
                    "code": "eu-west-1",
                    "status": "not-configured",
                    "last_sync": "-",
                    "duration": "-",
                    "cron": "-",
                    "concurrency": 0,
                    "resource_groups": [],
                },
            ],
        },
        {
            "name": "开发环境",
            "account_id": "555666777888",
            "coverage": "1/2",
            "regions": [
                {
                    "code": "ap-northeast-1",
                    "status": "synced",
                    "last_sync": "09:00-09:01",
                    "duration": "1m10s",
                    "cron": "0 9 * * *",
                    "concurrency": 10,
                    "resource_groups": [
                        {
                            "name": "计算",
                            "status": "success",
                            "resources": [
                                {"name": "EC2", "added": 3, "updated": 2, "deleted": 1},
                            ],
                        },
                    ],
                },
                {
                    "code": "us-east-1",
                    "status": "not-configured",
                    "last_sync": "-",
                    "duration": "-",
                    "cron": "-",
                    "concurrency": 0,
                    "resource_groups": [],
                },
            ],
        },
    ],
}

DEMO_HISTORY = {
    "records": [
        {"id": "#10342", "module": "AWS", "task": "生产-apne1 全量", "target": "生产 / apne1", "trigger": "Cron", "status": "success", "start": "15:26", "duration": "2m34s", "detail": "EC2↑5✏️3↓1, VPC不变"},
        {"id": "#10341", "module": "内部", "task": "钉钉审批增量", "target": "钉钉 OAPI", "trigger": "定时(15min)", "status": "success", "start": "15:30", "duration": "45s", "detail": "审批实例↑3✏️8"},
        {"id": "#10340", "module": "内部", "task": "Sentinel 告警", "target": "Sentinel API", "trigger": "定时(5min)", "status": "success", "start": "15:35", "duration": "6s", "detail": "2 活跃告警同步"},
        {"id": "#10339", "module": "AWS", "task": "生产-apse1 全量", "target": "生产 / apse1", "trigger": "Cron", "status": "running", "start": "15:29", "duration": "-", "detail": "运行中"},
        {"id": "#10338", "module": "AWS", "task": "生产-IAM 增量", "target": "生产 / global", "trigger": "人工", "status": "failed", "start": "15:20", "duration": "1m12s", "error": "AssumeRole 凭据过期", "detail": "IAM 全量同步失败"},
        {"id": "#10337", "module": "巡检", "task": "闲置资源检测", "target": "EC2/EBS/ELB", "trigger": "Cron", "status": "failed", "start": "07-22 06:00", "duration": "30m+", "error": "执行超时", "detail": "AssumeRole 轮换导致超时"},
        {"id": "#10336", "module": "内部", "task": "GitLab 仓库全量", "target": "GitLab API", "trigger": "Cron", "status": "failed", "start": "04:00", "duration": "-", "error": "Token 过期", "detail": "连接失败 — Token 过期"},
        {"id": "#10335", "module": "巡检", "task": "数据完整性检查", "target": "CMDB 全域", "trigger": "Cron", "status": "success", "start": "06:00", "duration": "4m20s", "detail": "23 条缺失关联"},
        {"id": "#10334", "module": "内部", "task": "企业微信全量", "target": "企微 API", "trigger": "Cron", "status": "success", "start": "05:00", "duration": "1m40s", "detail": "用户↑5✏️12↓1"},
        {"id": "#10333", "module": "内部", "task": "SonarQube 全量", "target": "SonarQube API", "trigger": "Cron", "status": "success", "start": "06:00", "duration": "2m12s", "detail": "42 项目报告"},
        {"id": "#10332", "module": "内部", "task": "Lark 通讯录全量", "target": "Lark Open API", "trigger": "Cron", "status": "success", "start": "04:00", "duration": "2m18s", "detail": "用户↑12✏️34↓2"},
        {"id": "#10331", "module": "巡检", "task": "安全组开放端口审计", "target": "1,250 安全组", "trigger": "Cron", "status": "success", "start": "07:00", "duration": "3m08s", "detail": "5 个安全组存在 0.0.0.0/0 入口"},
        {"id": "#10330", "module": "内部", "task": "Jira 工单同步", "target": "Jira REST API", "trigger": "每30min", "status": "success", "start": "15:22", "duration": "1m05s", "detail": "Issue↑8✏️15"},
        {"id": "#10329", "module": "内部", "task": "Jenkins 构建同步", "target": "Jenkins API", "trigger": "每10min", "status": "success", "start": "15:34", "duration": "8s", "detail": "156 Job·1,234 构建"},
        {"id": "#10328", "module": "巡检", "task": "成本异常分析", "target": "全账号 12 个", "trigger": "Cron", "status": "success", "start": "08:00", "duration": "1m12s", "detail": "生产周环比+12%"},
    ],
    "total": 342,
    "page": 1,
    "page_size": 50,
}


# ════════════════════════════════════════════════════════════════════
# 存储单例
# ════════════════════════════════════════════════════════════════════

class DemoStore:
    """模块级单例内存存储，提供与 API 视图对应的读取接口。"""

    def __init__(self):
        self._seeded = False
        # 使用可重入锁（RLock），避免 ensure_seeded → seed 嵌套加锁死锁
        self._lock = threading.RLock()
        self._data = {
            "stats": {},
            "workers": [],
            "load": "0%",
            "health": [],
            "freshness": {},
            "task_tree": {},
            "history": {},
            "task_trend": [],
            "recent_events": [],
            "resource_breakdown": [],
            "aws_resources": {},
        }

    # ── 播种 ──
    def seed(self, stats=None, workers=None, load=None, health=None,
             freshness=None, task_tree=None, history=None,
             task_trend=None, recent_events=None, resource_breakdown=None,
             aws_resources=None):
        """用演示数据填充存储（可整体替换或部分覆盖）。"""
        with self._lock:
            if stats is not None:
                self._data["stats"] = stats
            if workers is not None:
                self._data["workers"] = workers
            if load is not None:
                self._data["load"] = load
            if health is not None:
                self._data["health"] = health
            if freshness is not None:
                self._data["freshness"] = freshness
            if task_tree is not None:
                self._data["task_tree"] = task_tree
            if history is not None:
                self._data["history"] = history
            if task_trend is not None:
                self._data["task_trend"] = task_trend
            if recent_events is not None:
                self._data["recent_events"] = recent_events
            if resource_breakdown is not None:
                self._data["resource_breakdown"] = resource_breakdown
            if aws_resources is not None:
                self._data["aws_resources"] = aws_resources
            self._seeded = True
        return self

    def seed_defaults(self):
        return self.seed(
            stats=DEMO_STATS,
            workers=DEMO_WORKERS,
            load=DEMO_LOAD,
            health=DEMO_HEALTH,
            freshness=DEMO_FRESHNESS,
            task_tree=DEMO_TASK_TREE,
            history=DEMO_HISTORY,
            task_trend=DEMO_TASK_TREND,
            recent_events=DEMO_RECENT_EVENTS,
            resource_breakdown=DEMO_RESOURCE_BREAKDOWN,
            aws_resources=DEMO_AWS_RESOURCES,
        )

    def ensure_seeded(self):
        """首次访问时自动播种，保证幂等。"""
        with self._lock:
            if not self._seeded:
                self.seed_defaults()
        return self

    def reset(self):
        with self._lock:
            self._data = {k: ([] if isinstance(v, list) else {}) for k, v in self._data.items()}
            self._seeded = False

    # ── 读取接口 ──
    def get_stats(self) -> dict:
        self.ensure_seeded()
        return dict(self._data["stats"])

    def get_workers(self) -> list:
        self.ensure_seeded()
        return [dict(w) for w in self._data["workers"]]

    def get_load(self) -> str:
        self.ensure_seeded()
        return self._data["load"]

    def get_health(self) -> list:
        self.ensure_seeded()
        return [dict(h) for h in self._data["health"]]

    def get_freshness(self) -> dict:
        self.ensure_seeded()
        return dict(self._data["freshness"])

    def get_task_tree(self) -> dict:
        self.ensure_seeded()
        return self._data["task_tree"]

    def get_history(self) -> dict:
        self.ensure_seeded()
        return self._data["history"]

    def get_task_trend(self) -> list:
        self.ensure_seeded()
        return [dict(t) for t in self._data["task_trend"]]

    def get_recent_events(self) -> list:
        self.ensure_seeded()
        return [dict(e) for e in self._data["recent_events"]]

    def get_resource_breakdown(self) -> list:
        self.ensure_seeded()
        return [dict(r) for r in self._data["resource_breakdown"]]

    def get_aws_resources(self) -> dict:
        self.ensure_seeded()
        return self._data["aws_resources"]

    def append_history(self, record: dict):
        """Append a record to the history list (thread-safe)."""
        with self._lock:
            records = self._data["history"].setdefault("records", [])
            records.insert(0, record)
            self._data["history"]["total"] = self._data["history"].get("total", 0) + 1


# 模块级单例
demo_store = DemoStore()
