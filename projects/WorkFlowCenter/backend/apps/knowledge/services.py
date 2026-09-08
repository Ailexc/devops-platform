"""
系统知识库：文件驱动的文档服务

文档存储为独立 HTML 文件 + catalog.json 目录（分类/编排），
加载快、易维护，无需数据库。
"""
import json
from pathlib import Path

_DOCS_DIR = Path(__file__).resolve().parent / 'docs'


def _read_catalog():
    with open(_DOCS_DIR / 'catalog.json', encoding='utf-8') as f:
        return json.load(f)


def list_categories():
    """返回分类列表（含图标）"""
    cat = _read_catalog()
    return cat.get('categories', [])


def list_documents():
    """返回文档列表（不含正文，按目录 order 排序，保证分类分组顺序）"""
    cat = _read_catalog()
    docs = sorted(
        cat.get('documents', []),
        key=lambda d: d.get('order', 0),
    )
    return [{
        'key': d['key'],
        'title': d['title'],
        'category': d.get('category', ''),
        'summary': d.get('summary', ''),
        'icon': d.get('icon', ''),
        'order': d.get('order', 0),
    } for d in docs]


def get_document(key):
    """按 key 返回文档详情（含 HTML 正文）"""
    cat = _read_catalog()
    for d in cat.get('documents', []):
        if d['key'] == key:
            html_path = _DOCS_DIR / d.get('file', f"{d['key']}.html")
            if not html_path.exists():
                return None
            content = html_path.read_text(encoding='utf-8')
            return {
                'key': key,
                'title': d['title'],
                'category': d.get('category', ''),
                'summary': d.get('summary', ''),
                'icon': d.get('icon', ''),
                'content': content,
            }
    return None
