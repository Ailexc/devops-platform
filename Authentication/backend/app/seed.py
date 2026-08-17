"""种子数据：演示用户 + 应用注册表。"""
import logging
import os
import secrets

from .db import SessionLocal
from .models import AppRegistration, User
from .security import hash_password

logger = logging.getLogger("auth.seed")

# 演示账号（用户名 / 密码）
SEED_USERS = [
    {"username": "admin", "password": "admin1234", "display_name": "系统管理员",
     "email": "admin@devops.com", "department": "平台组", "is_admin": True, "source": "local"},
    {"username": "zhangsan", "password": "demo1234", "display_name": "张三",
     "email": "zhangsan@devops.com", "department": "研发部", "source": "local"},
    {"username": "lisi", "password": "demo1234", "display_name": "李四",
     "email": "lisi@devops.com", "department": "运维部", "source": "local"},
    {"username": "wangwu", "password": "demo1234", "display_name": "王五",
     "email": "wangwu@devops.com", "department": "测试部", "source": "local"},
]


def _home_url(app_id: str, default: str) -> str:
    """应用跳转地址：优先环境变量 APP_URL_<APP_ID>（云端部署覆盖），默认本地统一入口。"""
    return os.environ.get(f"APP_URL_{app_id.upper().replace('-', '_')}", default)


# 应用注册表（门户应用广场）
# access_mode：gateway=经统一网关 forwardAuth；direct=业务后端 JWKS 自验签
# home_url 说明：
#   - 6 个业务系统 → 统一网关 *.devops.orb.local（Phase 3，本地 OrbStack 自动 DNS）
#   - mock/direct（认证中心自带演示应用）→ authentication.orb.local 真实域名
#   - pilot/oidc 保持 localhost（认证流程演示，redirect_uri 与 home_url 强关联）
SEED_APPS = [
    {"app_id": "task-manager", "name": "任务管理 TaskManager", "description": "任务 / 工单管理平台",
     "icon": "CheckSquareOutlined", "home_url": _home_url("task-manager", "http://cmdb.devops.orb.local"), "sort_order": 1, "access_mode": "gateway"},
    {"app_id": "cloud-manager", "name": "多云管理 CloudManager", "description": "多云资源管理控制台",
     "icon": "CloudServerOutlined", "home_url": _home_url("cloud-manager", "http://cloud.devops.orb.local"), "sort_order": 2, "access_mode": "gateway"},
    {"app_id": "workflow-center", "name": "流程中心 WorkFlowCenter", "description": "流程编排与审批中心",
     "icon": "ApartmentOutlined", "home_url": _home_url("workflow-center", "http://workflow.devops.orb.local"), "sort_order": 3, "access_mode": "gateway"},
    {"app_id": "event-manager", "name": "事件管理 EventManager", "description": "告警与事件处理",
     "icon": "AlertOutlined", "home_url": _home_url("event-manager", "http://event.devops.orb.local"), "sort_order": 4, "access_mode": "direct"},
    {"app_id": "release-manager", "name": "发布管理 ReleaseManager", "description": "应用发布与部署",
     "icon": "RocketOutlined", "home_url": _home_url("release-manager", "http://release.devops.orb.local"), "sort_order": 5, "access_mode": "gateway"},
    {"app_id": "permission-center", "name": "权限中心 PermissionCenter", "description": "IAM 权限管控中心",
     "icon": "SafetyCertificateOutlined", "home_url": _home_url("permission-center", "http://iam.devops.orb.local"), "sort_order": 6, "access_mode": "gateway"},
    {"app_id": "mock-app", "name": "演示应用 MockApp", "description": "受统一网关 forwardAuth 保护的演示应用",
     "icon": "ExperimentOutlined", "home_url": _home_url("mock-app", "http://mock.authentication.orb.local"), "sort_order": 7, "access_mode": "gateway"},
    {"app_id": "direct-app", "name": "直连示例 DirectApp", "description": "不经网关，用 JWKS 公钥本地验签统一 JWT",
     "icon": "ApiOutlined", "home_url": _home_url("direct-app", "http://direct.authentication.orb.local"), "sort_order": 8, "access_mode": "direct"},
    {"app_id": "pilot-app", "name": "工单中心 PilotApp", "description": "试点接入示例：模拟真实业务系统接入统一认证",
     "icon": "DatabaseOutlined", "home_url": _home_url("pilot-app", "http://localhost:8004"), "sort_order": 9, "access_mode": "gateway"},
    {"app_id": "oidc-demo", "name": "OIDC 演示应用", "description": "演示 OIDC 授权码模式接入（code+client_secret 换 token）",
     "icon": "CodeOutlined", "home_url": _home_url("oidc-demo", "http://localhost:8005"), "sort_order": 10, "sso_type": "oidc", "access_mode": "direct",
     "client_id": "oidc-demo-app", "client_secret": "oidc-demo-secret-123456"},
]


def seed_all() -> None:
    db = SessionLocal()
    try:
        # 用户
        for u in SEED_USERS:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if exists is None:
                db.add(User(password_hash=hash_password(u["password"]), **{k: v for k, v in u.items() if k != "password"}))
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
                # 已存在：同步最新跳转地址（模板/环境变量变更后重启自动生效），保留凭证
                if exists.home_url != a["home_url"]:
                    exists.home_url = a["home_url"]
                    logger.info("同步应用 %s 跳转地址 → %s", a["app_id"], a["home_url"])
                if not exists.client_id:
                    # 老数据补齐凭证（保留显式配置的 OIDC 凭证）
                    exists.client_id = a.get("client_id") or f"{a['app_id']}-{secrets.token_hex(4)}"
                    exists.client_secret = a.get("client_secret") or secrets.token_urlsafe(24)
        db.commit()
        logger.info("种子数据就绪：%d 用户，%d 应用", len(SEED_USERS), len(SEED_APPS))
    finally:
        db.close()
