import os
import re
from datetime import datetime

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


DOCS_DIR = getattr(settings, "DOCS_DIR", "/tmp/cmdb_docs")


def _extract_title(html_content, filename):
    """Extract title from HTML <title> tag, fallback to filename."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return os.path.splitext(filename)[0].replace("-", " ").replace("_", " ").title()


def _scan_docs():
    """Scan docs directory and return list of document metadata."""
    docs = []
    if not os.path.isdir(DOCS_DIR):
        return docs

    for fname in sorted(os.listdir(DOCS_DIR)):
        if not fname.endswith((".html", ".htm")):
            continue
        fpath = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(fpath):
            continue

        stat = os.stat(fpath)
        # Try to extract title
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                head = f.read(4096)
            title = _extract_title(head, fname)
        except Exception:
            title = os.path.splitext(fname)[0]

        docs.append({
            "filename": fname,
            "title": title,
            "size": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })

    return docs


def _human_size(size):
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


@extend_schema(
    summary="文档列表",
    description="系统 HTML 文档列表",
    responses={200: OpenApiTypes.OBJECT},
)
class DocListView(APIView):
    """GET /api/v1/docs — list all HTML documents."""

    def get(self, request):
        docs = _scan_docs()
        return Response({"docs": docs, "total": len(docs)})


@extend_schema(
    summary="文档详情",
    description="返回单个 HTML 文档内容",
    responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
class DocDetailView(APIView):
    """GET /api/v1/docs/<filename> — return HTML content of a document."""

    def get(self, request, filename):
        if not filename.endswith((".html", ".htm")):
            return Response({"error": "Only HTML files are supported"}, status=status.HTTP_400_BAD_REQUEST)

        fpath = os.path.join(DOCS_DIR, filename)
        if not os.path.isfile(fpath):
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            title = _extract_title(content, filename)
            return Response({
                "filename": filename,
                "title": title,
                "content": content,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
