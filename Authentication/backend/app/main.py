"""统一认证中心 - FastAPI 应用入口。"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  确保模型注册
from .api import apps, auth, jwks, oauth, system, users
from .config import get_settings
from .db import Base, engine
from .seed import seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("auth")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="统一门户 + 登录认证 + SSO 多系统统一访问（Demo）",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# 本地开发允许跨域（OrbStack 同源部署时无需 CORS，浏览器视角同源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Auth-User", "X-Auth-Username", "X-Auth-Name", "X-Auth-Source"],
)

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(apps.router)
app.include_router(users.router)
app.include_router(system.router)
app.include_router(jwks.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_all()
    logger.info("统一认证中心启动完成：数据库已就绪，身份源顺序=%s", settings.auth_provider_order)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "jwks": "/.well-known/jwks.json",
        "health": "/api/system/health",
    }
