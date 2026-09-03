"""种子数据：演示用户 + 应用注册表。"""
import logging
import os
import secrets

from .db import SessionLocal
from .models import AppRegistration, User
from .security import hash_password

logger = logging.getLogger("auth.seed")

# 统一演示账号（全家桶固定用户体系，与 LDAP 目录一致；密码统一 demo1234）
# source=ldap：身份来自统一 LDAP 目录（本地保留同密码哈希，作为 LDAP 不可用时的 local 兜底）
# demo_systems：仅登录页下拉「按系统分组」的演示索引（用户真正归属是 department 组织，非系统）
SEED_USERS = [
    # 平台组 / 超管
    {"username": "admin", "password": "demo1234", "display_name": "系统管理员",
     "email": "admin@devops.com", "department": "平台组", "is_admin": True, "source": "ldap",
     "demo_systems": ["cloud-manager", "workflow-center", "permission-center", "task-manager", "event-manager", "release-manager"]},
    # 研发部
    {"username": "zhangsan", "password": "demo1234", "display_name": "张三",
     "email": "zhangsan@devops.com", "department": "研发部", "source": "ldap",
     "demo_systems": ["cloud-manager", "workflow-center", "task-manager", "event-manager"]},
    {"username": "xiaoming", "password": "demo1234", "display_name": "小明",
     "email": "xiaoming@devops.com", "department": "研发部", "source": "ldap",
     "demo_systems": ["workflow-center"]},
    {"username": "readonly", "password": "demo1234", "display_name": "只读用户",
     "email": "readonly@devops.com", "department": "研发部", "source": "ldap",
     "demo_systems": ["cloud-manager"]},
    # 运维部
    {"username": "lisi", "password": "demo1234", "display_name": "李四",
     "email": "lisi@devops.com", "department": "运维部", "source": "ldap",
     "demo_systems": ["cloud-manager", "workflow-center", "task-manager", "event-manager"]},
    {"username": "ops_user", "password": "demo1234", "display_name": "运维工程师",
     "email": "ops_user@devops.com", "department": "运维部", "source": "ldap",
     "demo_systems": ["cloud-manager", "event-manager"]},
    {"username": "xiaoli", "password": "demo1234", "display_name": "小李",
     "email": "xiaoli@devops.com", "department": "运维部", "source": "ldap",
     "demo_systems": ["workflow-center"]},
    # 测试部
    {"username": "wangwu", "password": "demo1234", "display_name": "王五",
     "email": "wangwu@devops.com", "department": "测试部", "source": "ldap",
     "demo_systems": ["task-manager", "event-manager"]},
    # 云平台组（云管 CloudManager 专属）
    {"username": "cloud_admin", "password": "demo1234", "display_name": "云管理员",
     "email": "cloud_admin@devops.com", "department": "云平台组", "source": "ldap",
     "demo_systems": ["cloud-manager"]},
    # 研发中心（权限中心 PermissionCenter）
    {"username": "alice", "password": "demo1234", "display_name": "爱丽丝",
     "email": "alice@devops.com", "department": "研发中心", "source": "ldap",
     "demo_systems": ["permission-center", "cloud-manager"]},
    {"username": "bob", "password": "demo1234", "display_name": "鲍勃",
     "email": "bob@devops.com", "department": "研发中心", "source": "ldap",
     "demo_systems": ["permission-center"]},
    # 运维平台（权限中心 PermissionCenter）
    {"username": "erin", "password": "demo1234", "display_name": "艾琳",
     "email": "erin@devops.com", "department": "运维平台", "source": "ldap",
     "demo_systems": ["permission-center", "event-manager"]},
]


def _home_url(app_id: str, default: str) -> str:
    """应用跳转地址：优先环境变量 APP_URL_<APP_ID>（云端部署覆盖），默认本地统一入口。"""
    return os.environ.get(f"APP_URL_{app_id.upper().replace('-', '_')}", default)


def _portal_url(default: str = "http://portal.authentication.orb.local") -> str:
    """门户地址：优先 PORTAL_URL（云端部署覆盖）。"""
    return os.environ.get("PORTAL_URL", default)


# 应用注册表（门户应用广场）
# access_mode：gateway=经统一网关 forwardAuth；direct=业务后端 JWKS 自验签 / OIDC 客户端
# home_url 说明：
#   - 6 个业务系统 → 统一网关 *.devops.orb.local（Phase 3，本地 OrbStack 自动 DNS）
#   - mock/direct（认证中心自带演示应用）→ authentication.orb.local 真实域名
#   - pilot/oidc 保持 localhost（认证流程演示，redirect_uri 与 home_url 强关联）
# redirect_uris：OIDC 授权码回调白名单（精确匹配）；非 OIDC 应用可留空（内部信任域 token 透传）
SEED_APPS = [
    {"app_id": "task-manager", "name": "任务管理 TaskManager", "description": "任务管理平台（任务编排与调度）",
     "icon": "ScheduleOutlined", "home_url": _home_url("task-manager", "http://cmdb.devops.orb.local"), "sort_order": 1, "access_mode": "direct", "redirect_uris": []},
    {"app_id": "cloud-manager", "name": "多云管理 CloudManager", "description": "多云资源管理控制台",
     "icon": "CloudServerOutlined", "home_url": _home_url("cloud-manager", "http://cloud.devops.orb.local"), "sort_order": 2, "access_mode": "gateway", "redirect_uris": []},
    {"app_id": "workflow-center", "name": "工单中心 WorkFlowCenter", "description": "工单 / 流程管理平台",
     "icon": "ApartmentOutlined", "home_url": _home_url("workflow-center", "http://workflow.devops.orb.local"), "sort_order": 3, "access_mode": "gateway", "redirect_uris": []},
    {"app_id": "event-manager", "name": "事件管理 EventManager", "description": "告警与事件处理",
     "icon": "AlertOutlined", "home_url": _home_url("event-manager", "http://event.devops.orb.local"), "sort_order": 4, "access_mode": "direct", "redirect_uris": []},
    {"app_id": "release-manager", "name": "发布管理 ReleaseManager", "description": "应用发布与部署",
     "icon": "RocketOutlined", "home_url": _home_url("release-manager", "http://release.devops.orb.local"), "sort_order": 5, "sso_type": "oidc", "access_mode": "direct",
     "client_id": "release-manager-app", "client_secret": "release-secret-123456",
     "redirect_uris": [f"{_home_url('release-manager', 'http://release.devops.orb.local')}/oauth/callback"],
     "allowed_scopes": ["openid", "profile", "email"]},
    {"app_id": "permission-center", "name": "权限中心 PermissionCenter", "description": "IAM 权限管控中心",
     "icon": "SafetyCertificateOutlined", "home_url": _home_url("permission-center", "http://iam.devops.orb.local"), "sort_order": 6, "access_mode": "gateway", "redirect_uris": []},
    {"app_id": "mock-app", "name": "演示应用 MockApp", "description": "受统一网关 forwardAuth 保护的演示应用",
     "icon": "ExperimentOutlined", "home_url": _home_url("mock-app", "http://mock.authentication.orb.local"), "sort_order": 7, "access_mode": "gateway", "redirect_uris": []},
    {"app_id": "direct-app", "name": "直连示例 DirectApp", "description": "不经网关，用 JWKS 公钥本地验签统一 JWT",
     "icon": "ApiOutlined", "home_url": _home_url("direct-app", "http://direct.authentication.orb.local"), "sort_order": 8, "access_mode": "direct", "redirect_uris": []},
    {"app_id": "pilot-app", "name": "工单中心 PilotApp", "description": "试点接入示例：模拟真实业务系统接入统一认证",
     "icon": "DatabaseOutlined", "home_url": _home_url("pilot-app", "http://localhost:8004"), "sort_order": 9, "access_mode": "gateway", "redirect_uris": []},
    {"app_id": "oidc-demo", "name": "OIDC 演示应用", "description": "演示 OIDC 授权码模式接入（code+client_secret 换 token）",
     "icon": "CodeOutlined", "home_url": _home_url("oidc-demo", "http://localhost:8005"), "sort_order": 10, "sso_type": "oidc", "access_mode": "direct",
     "client_id": "oidc-demo-app", "client_secret": "oidc-demo-secret-123456",
     "redirect_uris": [f"{_home_url('oidc-demo', 'http://localhost:8005')}/callback"],
     "allowed_scopes": ["openid", "profile", "email"]},
    # 统一门户：作为认证中心的第一个 OIDC 客户端（RP），走「门户 BFF + PKCE」标准授权码流
    {"app_id": "portal", "name": "统一门户 Portal", "description": "统一门户（OIDC 客户端，BFF 模式接入）",
     "icon": "AppstoreOutlined", "home_url": _portal_url(), "sort_order": 0, "sso_type": "oidc", "access_mode": "direct",
     "client_id": "portal-app", "client_secret": "portal-secret-123456",
     "redirect_uris": [f"{_portal_url()}/portal/oauth/callback"],
     "allowed_scopes": ["openid", "profile", "email"]},
]


def seed_all() -> None:
    db = SessionLocal()
    try:
        # 用户（统一目录同步：不存在则创建，已存在则以 SEED_USERS 为准刷新密码/组织/演示分组）
        for u in SEED_USERS:
            fields = {k: v for k, v in u.items() if k != "password"}
            exists = db.query(User).filter(User.username == u["username"]).first()
            if exists is None:
                db.add(User(password_hash=hash_password(u["password"]), **fields))
            else:
                exists.password_hash = hash_password(u["password"])
                exists.display_name = fields.get("display_name") or exists.display_name
                exists.email = fields.get("email") or exists.email
                exists.department = fields.get("department") or exists.department
                exists.is_admin = fields.get("is_admin", exists.is_admin)
                exists.source = fields.get("source", exists.source)
                if fields.get("demo_systems"):
                    exists.demo_systems = fields["demo_systems"]
        # 应用
        for a in SEED_APPS:
            exists = db.query(AppRegistration).filter(AppRegistration.app_id == a["app_id"]).first()
            if exists is None:
                cid = a.get("client_id") or f"{a['app_id']}-{secrets.token_hex(4)}"
                csec = a.get("client_secret") or secrets.token_urlsafe(24)
                db.add(AppRegistration(
                    client_id=cid,
                    client_secret=csec,
                    **{k: v for k, v in a.items() if k not in ("client_id", "client_secret")},
                ))
            else:
                # 已存在：以 SEED_APPS 为权威配置同步（名称/描述/图标/接入方式/跳转地址），保留已显式配置的 OIDC 凭证
                sync_fields = ["name", "description", "icon", "sso_type", "access_mode"]
                for f in sync_fields:
                    if a.get(f) is not None and getattr(exists, f) != a[f]:
                        setattr(exists, f, a[f])
                        logger.info("同步应用 %s %s → %s", a["app_id"], f, a[f])
                if exists.home_url != a["home_url"]:
                    exists.home_url = a["home_url"]
                    logger.info("同步应用 %s 跳转地址 → %s", a["app_id"], a["home_url"])
                # OIDC 客户端凭证由 SEED_APPS 权威管理（演示环境强制对齐，避免随机后缀漂移）
                if a.get("sso_type") == "oidc" and a.get("client_id"):
                    if exists.client_id != a["client_id"]:
                        exists.client_id = a["client_id"]
                        logger.info("同步应用 %s client_id → %s", a["app_id"], a["client_id"])
                    if a.get("client_secret") and exists.client_secret != a["client_secret"]:
                        exists.client_secret = a["client_secret"]
                        logger.info("同步应用 %s client_secret", a["app_id"])
                    if a.get("redirect_uris") and exists.redirect_uris != a["redirect_uris"]:
                        exists.redirect_uris = a["redirect_uris"]
                        logger.info("同步应用 %s redirect_uris", a["app_id"])
                if not exists.client_id:
                    # 老数据补齐凭证（保留显式配置的 OIDC 凭证）
                    exists.client_id = a.get("client_id") or f"{a['app_id']}-{secrets.token_hex(4)}"
                    exists.client_secret = a.get("client_secret") or secrets.token_urlsafe(24)
                # 老数据补齐 OIDC 白名单（新增列默认空，二次启动自动补齐）
                if not exists.redirect_uris and a.get("redirect_uris"):
                    exists.redirect_uris = a["redirect_uris"]
                    logger.info("同步应用 %s redirect_uris → %s", a["app_id"], a["redirect_uris"])
                if not exists.allowed_scopes and a.get("allowed_scopes"):
                    exists.allowed_scopes = a["allowed_scopes"]
        db.commit()
        logger.info("种子数据就绪：%d 用户，%d 应用", len(SEED_USERS), len(SEED_APPS))
    finally:
        db.close()
