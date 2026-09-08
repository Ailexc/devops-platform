from ninja import NinjaAPI
from api.v1.events import router as events_router
from api.v1.stats import router as stats_router
from api.v1.handlers import router as handlers_router
from api.v1.test_lab import router as test_lab_router
from api.v1.docs import router as docs_router
from api.v1.auth import router as auth_router

api = NinjaAPI(
    title="EventFlow API",
    version="0.1.0",
    description="事件管理系统 API",
)

api.add_router("/v1/auth", auth_router, tags=["统一认证"])
api.add_router("/v1/events", events_router, tags=["事件"])
api.add_router("/v1/stats", stats_router, tags=["统计"])
api.add_router("/v1/handlers", handlers_router, tags=["Handler"])
api.add_router("/v1/test-lab", test_lab_router, tags=["测试模块"])
api.add_router("/v1/docs", docs_router, tags=["系统文档"])
