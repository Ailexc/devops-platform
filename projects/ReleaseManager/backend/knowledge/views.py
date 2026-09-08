"""
Knowledge API — 文件系统驱动的知识库

设计原则:
  - docs/ 目录即数据源
  - 新增/删除文件 = 新增/删除文章
  - meta.json 驱动卡片展示
  - HTML 直接返回，前端渲染
  - 面试题 Markdown 支持编辑保存
"""

import json
import os
from pathlib import Path

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

DOCS_ROOT = Path(__file__).parent / "docs"


def _get_modules():
    """
    扫描 docs/ 返回模块列表

    模块 = docs/ 下的子目录，自动发现。
    文章 = articles/ 目录中的文件，按文件名（去扩展名）作为 ID。
    meta.json 仅提供显示元数据（名称、描述、图标、排序、文章标题/标签等）,
    不控制文件是否存在。
    """
    modules = []
    if not DOCS_ROOT.exists():
        return modules

    for entry in sorted(DOCS_ROOT.iterdir()):
        if not entry.is_dir():
            continue

        # 读取元数据
        meta_file = entry / "meta.json"
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                meta = {}

        # 扫描 articles/ 目录获取实际文件列表
        articles_dir = entry / "articles"
        articles_list = []
        if articles_dir.exists():
            for f in sorted(articles_dir.iterdir()):
                if f.suffix.lower() in (".html", ".htm", ".md"):
                    article_id = f.stem  # 文件名（不含扩展名）
                    # 从 meta.json 中取元数据（如果有）
                    article_meta = meta.get("articles", {}).get(article_id, {})
                    articles_list.append({
                        "id": article_id,
                        "title": article_meta.get("title", article_id),
                        "description": article_meta.get("description", ""),
                        "tags": article_meta.get("tags", []),
                        "updated": article_meta.get("updated", ""),
                    })

        interviews_dir = entry / "interviews"
        has_interview = interviews_dir.exists() and bool(list(interviews_dir.glob("*.md")))

        modules.append({
            "id": entry.name,
            "name": meta.get("name", entry.name),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "📄"),
            "sort": meta.get("sort", 99),
            "article_count": len(articles_list),
            "interview_count": 0,
            "articles": articles_list,
            "has_interview": has_interview,
        })

    return sorted(modules, key=lambda m: m["sort"])


def _count_interviews(module_id):
    """统计模块面试题数"""
    d = DOCS_ROOT / module_id / "interviews"
    if not d.exists():
        return 0
    count = 0
    for f in d.glob("*.md"):
        try:
            c = f.read_text(encoding="utf-8")
            count += c.count("\n## ")
        except IOError:
            pass
    return count


@api_view(["GET"])
def module_list(request):
    """知识库模块列表"""
    modules = _get_modules()
    for m in modules:
        m["interview_count"] = _count_interviews(m["id"])
    return Response({"code": 200, "data": modules})


@api_view(["GET"])
def module_detail(request, module_id):
    """单个模块详情"""
    modules = _get_modules()
    mod = next((m for m in modules if m["id"] == module_id), None)
    if not mod:
        return Response({"code": 404, "message": "模块不存在"}, status=404)
    mod["interview_count"] = _count_interviews(mod["id"])
    return Response({"code": 200, "data": mod})


@api_view(["GET"])
def article_content(request, module_id, article_id):
    """文章内容（HTML/MD）"""
    # 读取 meta.json 获取元信息
    meta_file = DOCS_ROOT / module_id / "meta.json"
    meta = {}
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    article_meta = meta.get("articles", {}).get(article_id, {})

    articles_dir = DOCS_ROOT / module_id / "articles"
    content = None
    file_path = None

    for ext in [".html", ".htm", ".md"]:
        candidate = articles_dir / f"{article_id}{ext}"
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8")
                file_path = candidate
            except IOError:
                pass

    if content is None:
        return Response({"code": 404, "message": "文章不存在"}, status=404)

    ext = file_path.suffix.lower() if file_path else ".html"
    fmt = "html" if ext in (".html", ".htm") else "markdown"

    return Response({
        "code": 200,
        "data": {
            "id": article_id,
            "title": article_meta.get("title", article_id),
            "description": article_meta.get("description", ""),
            "tags": article_meta.get("tags", []),
            "updated": article_meta.get("updated", ""),
            "format": fmt,
            "content": content,
        },
    })


@api_view(["GET", "PUT"])
def interview_content(request, module_id):
    """面试题 Markdown 读/写"""
    interviews_dir = DOCS_ROOT / module_id / "interviews"

    if request.method == "GET":
        if not interviews_dir.exists():
            return Response({"code": 404, "message": "暂无面试题"}, status=404)
        md_files = list(interviews_dir.glob("*.md"))
        if not md_files:
            return Response({"code": 404, "message": "暂无面试题"}, status=404)
        try:
            content = md_files[0].read_text(encoding="utf-8")
        except IOError:
            return Response({"code": 500, "message": "读取失败"}, status=500)
        return Response({
            "code": 200,
            "data": {
                "module_id": module_id,
                "filename": md_files[0].name,
                "content": content,
            },
        })

    # PUT
    content = request.data.get("content", "")
    filename = request.data.get("filename", "README.md")
    if not interviews_dir.exists():
        interviews_dir.mkdir(parents=True)
    file_path = interviews_dir / filename
    try:
        file_path.write_text(content, encoding="utf-8")
    except IOError:
        return Response({"code": 500, "message": "保存失败"}, status=500)
    return Response({"code": 200, "message": "保存成功"})


@api_view(["GET"])
def yuque_config(request):
    """获取语雀面试宝典配置"""
    config_file = DOCS_ROOT / "yuque-config.json"
    if not config_file.exists():
        return Response({
            "code": 200,
            "data": {
                "url": "",
                "title": "未配置",
                "description": "请联系管理员配置语雀面试宝典链接",
                "open_mode": "new_tab",
                "configured": False,
            },
        })
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
        config["configured"] = True
    except (json.JSONDecodeError, IOError):
        return Response({"code": 500, "message": "配置读取失败"}, status=500)
    return Response({"code": 200, "data": config})
