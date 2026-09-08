"""
系统文档模块 —— 展示项目 docs 目录下的 HTML 文档

- GET /api/v1/docs          → 列出所有 HTML 文档（文件名 / 标题 / 描述 / 大小 / 修改时间）
- GET /api/v1/docs/{name}   → 返回文档 HTML 内容（可直接在 iframe 中渲染）
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from ninja import Router
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = Router()

# docs 目录：优先使用环境变量（Docker 中 /app/docs），本地开发默认 backend/docs/
DOCS_DIR = Path(
    os.getenv("DOCS_DIR", str(Path(__file__).resolve().parent.parent.parent / "docs"))
)


class DocInfo(BaseModel):
    filename: str
    title: str
    description: str
    size: int
    modified_at: str


def _extract_meta(filename: str, content: str) -> tuple[str, str]:
    """从 HTML 中提取标题与描述"""
    title = filename
    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()

    description = ""
    # 优先取 <meta name="description">，其次取第一个 <p>
    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        content, re.IGNORECASE | re.DOTALL,
    )
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        p_match = re.search(r"<p[^>]*>(.*?)</p>", content, re.IGNORECASE | re.DOTALL)
        if p_match:
            description = re.sub(r"<[^>]+>", "", p_match.group(1)).strip()
    return title, description[:200]


@router.get("", response=list[DocInfo])
def list_docs(request):
    """列出 docs 目录下所有 HTML 文档"""
    if not DOCS_DIR.exists():
        return []
    docs = []
    for f in sorted(DOCS_DIR.glob("*.html")):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("读取文档 %s 失败: %s", f.name, exc)
            continue
        title, description = _extract_meta(f.name, content)
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        docs.append(
            DocInfo(
                filename=f.name,
                title=title,
                description=description,
                size=f.stat().st_size,
                modified_at=mtime.strftime("%Y-%m-%d %H:%M"),
            )
        )
    return docs


@router.get("/{filename}")
@xframe_options_exempt
def get_doc(request, filename: str):
    """返回文档 HTML 内容（允许 iframe 渲染）"""
    # 安全检查：仅允许 .html 文件，禁止路径穿越
    if not filename.endswith(".html") or "/" in filename or "\\" in filename or ".." in filename:
        return HttpResponse("非法文件名", status=400)
    file_path = (DOCS_DIR / filename).resolve()
    if not str(file_path).startswith(str(DOCS_DIR.resolve())):
        return HttpResponse("非法文件路径", status=400)
    if not file_path.exists():
        return HttpResponse("文档不存在", status=404)

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return HttpResponse("读取文档失败", status=500)
    return HttpResponse(content, content_type="text/html; charset=utf-8")
