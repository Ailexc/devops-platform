from fastapi import FastAPI
import os
import platform

app = FastAPI(title="Python Demo App", version="1.0.0")

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_NAME = os.getenv("APP_NAME", "python-demo")
ENV = os.getenv("ENV", "dev")

@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "env": ENV,
        "language": "Python",
        "host": platform.node(),
    }

@app.get("/health")
async def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}

@app.get("/info")
async def info():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "env": ENV,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }