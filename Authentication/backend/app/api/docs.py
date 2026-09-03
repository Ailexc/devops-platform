"""系统文档接口 —— 门户内置的 HTML 文档库。

文档以 HTML 片段形式存放在后端 `app/system_docs/` 目录下（随镜像打包，固化用于阅读与学习）。
前端系统文档板块通过本路由获取文档清单与文档内容，自行渲染排版与目录。

路由：
  GET /system-docs/index.json   -> 文档清单（标题/简介/分类/封面图标）
  GET /system-docs/{doc_id}     -> 返回 HTML 文档内容（text/html）
"""
import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/system-docs", tags=["system-docs"])

# 文档目录：backend/app/system_docs/
DOCS_DIR = Path(__file__).resolve().parent.parent / "system_docs"
_INDEX = None

# 只允许纯字母数字与连字符的文档 id，杜绝路径穿越
_SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def _index_data() -> dict:
    """读取并缓存文档清单。"""
    global _INDEX
    if _INDEX is None:
        idx_path = DOCS_DIR / "index.json"
        if not idx_path.exists():
            raise HTTPException(status_code=500, detail="系统文档清单缺失")
        _INDEX = json.loads(idx_path.read_text(encoding="utf-8"))
    return _INDEX


@router.get("/index.json", summary="系统文档清单")
def index():
    return _index_data()


@router.get("/{doc_id}", response_class=HTMLResponse, summary="获取 HTML 文档内容")
def get_doc(doc_id: str):
    if not _SAFE_ID.match(doc_id):
        raise HTTPException(status_code=400, detail="非法的文档标识")
    # 文档必须登记在清单中，才允许访问
    doc_ids = {d["id"] for d in _index_data()["docs"]}
    if doc_id not in doc_ids:
        raise HTTPException(status_code=404, detail="文档不存在")
    file_path = DOCS_DIR / f"{doc_id}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文档内容缺失")
    return HTMLResponse(content=file_path.read_text(encoding="utf-8"))
