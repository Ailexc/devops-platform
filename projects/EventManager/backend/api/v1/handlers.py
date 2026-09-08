from ninja import Router
from apps.event_store.models import EventHandlerConfig
from handlers.registry import EVENT_TYPE_INFO

router = Router()


@router.get("", response=list[dict])
def list_handlers(request):
    """列出所有已注册 Handler（数据库配置）"""
    configs = EventHandlerConfig.objects.filter(is_active=True)
    return [
        {
            "id": c.id,
            "name": c.name,
            "event_type_pattern": c.event_type_pattern,
            "handler_class": c.handler_class,
            "timeout": c.timeout,
            "max_retries": c.max_retries,
        }
        for c in configs
    ]


@router.get("/event-types", response=list[dict])
def list_event_types(request):
    """列出系统支持的所有事件类型（代码注册）"""
    return EVENT_TYPE_INFO

