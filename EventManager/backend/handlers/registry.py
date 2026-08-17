import logging

from core.router import registry
from handlers.internal.echo_handler import EchoHandler
from handlers.internal.health_handler import HealthCheckHandler
from handlers.aws.ec2_handler import EC2StateChangeHandler
from handlers.aws.rds_handler import RDSEventHandler
from handlers.aws.s3_handler import S3NotificationHandler
from handlers.webhook.github_handler import GitHubWebhookHandler

logger = logging.getLogger(__name__)


# 事件类型元数据（从 Handler 类的 display 属性读取）
def _build_event_type_info() -> list[dict]:
    """从各 Handler 的 display 属性构建事件类型信息"""
    handlers = [
        ("AWS EC2", "🖥️", "aws.ec2.*", "EC2 实例状态变更事件", EC2StateChangeHandler),
        ("AWS RDS", "🗄️", "aws.rds.*", "RDS 数据库事件，包括创建、备份、故障转移、扩缩容", RDSEventHandler),
        ("AWS S3", "📦", "aws.s3.*", "S3 对象操作事件，文件上传、删除、恢复等", S3NotificationHandler),
        ("Webhook", "🔗", "webhook.github.*", "GitHub Webhook 事件，支持 push、PR、issue、release 等", GitHubWebhookHandler),
        ("内部监控", "💚", "internal.health", "内部健康检查事件，定时检测各服务状态", HealthCheckHandler),
        ("调试测试", "🧪", "echo.*", "Demo 回显测试事件，用于开发和调试", EchoHandler),
    ]
    result = []
    for category, icon, pattern, description, handler_cls in handlers:
        entry = {
            "category": category,
            "icon": icon,
            "pattern": pattern,
            "description": description,
            "handler": handler_cls.__name__,
        }
        if hasattr(handler_cls, "display"):
            entry.update(handler_cls.display)
        result.append(entry)
    return result


EVENT_TYPE_INFO = _build_event_type_info()


def register_all() -> None:
    """注册所有内置 Handler"""
    registry.register("aws.ec2.*", EC2StateChangeHandler)
    registry.register("aws.rds.*", RDSEventHandler)
    registry.register("aws.s3.*", S3NotificationHandler)
    registry.register("webhook.github.*", GitHubWebhookHandler)
    registry.register("internal.health", HealthCheckHandler)
    registry.register("echo.*", EchoHandler)
    registry.register("*", EchoHandler)  # 兜底: 所有未匹配事件走 Echo
    logger.info("Registered %d event handlers", len(registry._handlers) - 1)

    logger.info("Registered %d built-in handlers", len(registry._handlers))
