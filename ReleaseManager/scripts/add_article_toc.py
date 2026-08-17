#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为知识库文章 HTML 注入「自包含」的左侧章节导航。

背景:
    以前文章导航由前端 (docs.tsx) 通过正则从 HTML 中抽取 h2 生成,
    存在「目录识别不准、占用空间、与文章文件脱节」的问题。
    现在把导航直接写进文章 HTML 文件内部:
      - 统一的章节 id 锚点 (保留已有 id, 缺失的自动生成 sec-N)
      - 左侧 sticky 目录 <nav> (链接到各章节锚点)
      - 滚动高亮当前章节 (IntersectionObserver 降级为 scroll 监听)
      - 可折叠按钮 (收起/展开目录, 不占空间)
      - 移除文章内冗余的手写「目录」块
    前端只负责用 iframe 把整份 HTML 原样渲染。

幂等: 已包含 class="doc-layout" 的文件会被跳过。
用法: python scripts/add_article_toc.py
"""

import re
from pathlib import Path
from typing import Optional

DOCS_ROOT = Path(__file__).resolve().parent.parent / "backend" / "knowledge" / "docs"

# ---------- 注入的样式 / 脚本 ----------

TOC_CSS = """
/* ===== 文章自包含导航 (由 add_article_toc.py 注入) ===== */
/* 注意: 不使用 scroll-behavior: smooth，srcdoc sandbox iframe 内动画会导致 scroll 事件不可靠 */
[id] { scroll-margin-top: 14px; }
.doc-layout { display: flex; gap: 28px; align-items: flex-start; }
.doc-toc {
  width: 236px; flex-shrink: 0; box-sizing: border-box;
  position: sticky; top: 0; max-height: 100vh; overflow-y: auto;
  padding: 8px 4px 24px 0; border-right: 1px solid #eef0f6;
}
.doc-toc.is-hidden { display: none; }
.doc-toc-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 10px 10px; font-size: 13px; font-weight: 700; color: #4a5568;
  letter-spacing: .5px;
}
.doc-toc-hide {
  cursor: pointer; border: none; background: transparent; color: #a0aec0;
  font-size: 14px; line-height: 1; padding: 2px 6px; border-radius: 4px;
}
.doc-toc-hide:hover { color: #1a202c; background: #f1f5f9; }
.doc-toc-nav { display: flex; flex-direction: column; gap: 1px; }
.doc-toc-nav a {
  display: block; padding: 6px 10px; border-left: 3px solid transparent;
  border-radius: 0 6px 6px 0; color: #4a5568; text-decoration: none;
  font-size: 13px; line-height: 1.5; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; transition: all .15s;
}
.doc-toc-nav a:hover { color: #1677ff; background: #f0f6ff; }
.doc-toc-nav a.active {
  color: #1677ff; background: #e6f4ff; border-left-color: #1677ff; font-weight: 600;
}
.doc-toc-show {
  display: none; position: sticky; top: 8px; z-index: 30;
  border: 1px solid #c7d7f5; background: #fff; color: #1677ff;
  font-size: 13px; border-radius: 8px; padding: 6px 12px; cursor: pointer;
  box-shadow: 0 2px 8px rgba(22,119,255,.15);
}
.doc-toc-show.is-visible { display: inline-block; }
.doc-main { flex: 1; min-width: 0; }
@media (max-width: 820px) {
  .doc-layout { flex-direction: column; gap: 12px; }
  .doc-toc {
    position: static; width: 100%; max-height: 220px;
    border-right: none; border-bottom: 1px solid #eef0f6;
  }
}
"""

TOC_JS = """
<script>
(function () {
  var toc = document.getElementById('doc-toc');
  var showBtn = document.getElementById('doc-toc-show');
  var hideBtn = document.getElementById('doc-toc-hide');
  var links = Array.prototype.slice.call(
    document.querySelectorAll('.doc-toc-nav a[href^="#"]')
  );
  var items = links.map(function (a) {
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    return el ? { id: id, el: el, a: a } : null;
  }).filter(Boolean);
  if (!items.length) { return; }

  function highlight() {
    var pos = window.scrollY + 120;
    var active = null;
    for (var i = 0; i < items.length; i++) {
      var top = items[i].el.getBoundingClientRect().top + window.scrollY;
      if (top <= pos) { active = items[i].id; }
    }
    var activeEl = active ? items.filter(function (x) { return x.id === active; })[0].a : null;
    items.forEach(function (x) {
      x.a.classList.toggle('active', x.a === activeEl);
    });
  }
  // srcdoc sandbox iframe 内 scroll/IntersectionObserver 事件不可靠，
  // 故用轮询驱动高亮，scroll/resize 事件仅作加速。
  window.setInterval(highlight, 150);
  window.addEventListener('scroll', highlight, { passive: true });
  window.addEventListener('resize', highlight, { passive: true });
  highlight();

  // 拦截目录链接点击：srcdoc iframe 内原生锚点 <a href="#id"> 会解析到
  // 父页面 URL 而被沙箱拦截，必须改用 scrollIntoView 实现平滑/即时跳转。
  links.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var id = a.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (el) el.scrollIntoView(true);
    });
  });

  if (hideBtn && toc) {
    hideBtn.addEventListener('click', function () {
      toc.classList.add('is-hidden');
      if (showBtn) showBtn.classList.add('is-visible');
    });
  }
  if (showBtn) {
    showBtn.addEventListener('click', function () {
      if (toc) toc.classList.remove('is-hidden');
      showBtn.classList.remove('is-visible');
    });
  }
})();
</script>
"""

# ---------- 正则 ----------

H2_RE = re.compile(r"<h2\b[^>]*>.*?</h2>", re.DOTALL | re.IGNORECASE)
H2_TAG_RE = re.compile(r"<h2\b([^>]*)>", re.IGNORECASE)
ATTR_ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
TAG_STRIP_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SECTION_RE = re.compile(r"<section\b[^>]*>", re.IGNORECASE)
SECTION_END_RE = re.compile(r"</section\s*>", re.IGNORECASE)

MANUAL_TOC_LABELS = {"目录", "📑 目录", "📖 目录", "文章目录"}


def clean_label(inner: str) -> str:
    """去掉标签、折叠空白，得到纯文本标题。"""
    text = TAG_STRIP_RE.sub("", inner)
    text = WS_RE.sub(" ", text).strip()
    return text


def find_section_id(html: str, h2_start: int, section_ends: list) -> Optional[str]:
    """
    若 h2 被 <section id="..."> 包裹，则返回该 section 的 id。
    section 不嵌套，start/end 按顺序一一对应。
    """
    for i, m in enumerate(SECTION_RE.finditer(html)):
        end_pos = section_ends[i] if i < len(section_ends) else len(html)
        if m.start() > h2_start:
            break
        if m.start() < h2_start < end_pos:
            mid = ATTR_ID_RE.search(m.group(0))
            if mid:
                return mid.group(1)
            return None
    return None


def remove_manual_toc(html: str) -> str:
    """移除文章内手写的 <div class="toc">...</div> 目录块（含其上方注释行）。"""
    marker = re.compile(
        r'(?:<!--[^\n]*-->\s*)?<div\s+class=["\']toc["\'][^>]*>', re.IGNORECASE
    )
    m = marker.search(html)
    if not m:
        return html
    start = m.start()
    # 平衡 <div>/</div> 找到外层闭合
    opens = 0
    pos = m.end()
    div_open = re.compile(r"<div\b", re.IGNORECASE)
    div_close = re.compile(r"</div\s*>", re.IGNORECASE)
    cursor = pos
    while True:
        o = div_open.search(html, cursor)
        c = div_close.search(html, cursor)
        if c is None:
            break
        if o is not None and o.start() < c.start():
            opens += 1
            cursor = o.end()
        else:
            opens -= 1
            cursor = c.end()
            if opens <= 0:
                end = c.end()
                break
    else:
        return html
    # 一并去掉紧随其后的空行
    tail = html[end:]
    tail = re.sub(r"^\s*\n", "", tail)
    return html[:start] + tail


def process_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    if 'class="doc-layout"' in html:
        print(f"  [跳过] 已处理过: {path.name}")
        return False

    # 移除手写目录块（若有）
    html = remove_manual_toc(html)

    # 1) 收集 h2 锚点
    section_ends = [m.start() for m in SECTION_END_RE.finditer(html)]
    existing_ids = set(ATTR_ID_RE.findall(html))
    headings = []  # {start, end, attrs, id, label, inject}
    generated = 0

    for m in H2_RE.finditer(html):
        tag = H2_TAG_RE.match(m.group(0))
        attrs = tag.group(1) if tag else ""
        inner = m.group(0)[tag.end():]
        inner = re.sub(r"</h2\s*>$", "", inner, flags=re.IGNORECASE).rstrip()
        label = clean_label(inner)
        if not label or label in MANUAL_TOC_LABELS:
            continue

        id_attr = ATTR_ID_RE.search(attrs)
        if id_attr:
            hid = id_attr.group(1)
            inject = False
        else:
            hid = find_section_id(html, m.start(), section_ends)
            inject = hid is None  # 若 section 已提供 id，无需改 h2
            if hid is None:
                generated += 1
                hid = f"sec-{generated}"
                while hid in existing_ids:
                    generated += 1
                    hid = f"sec-{generated}"
                existing_ids.add(hid)

        headings.append({
            "start": m.start(),
            "tag_end": m.start() + tag.end() if tag else m.start(),
            "attrs": attrs,
            "id": hid,
            "label": label,
            "inject": inject,
        })

    if not headings:
        print(f"  [跳过] 无 h2 章节: {path.name}")
        return False

    # 2) 给缺失 id 的 h2 注入 id（逆序替换，保证偏移不失效）
    for h in sorted(headings, key=lambda x: x["start"], reverse=True):
        if h["inject"]:
            new_tag = f'<h2{h["attrs"]} id="{h["id"]}">'
            html = html[: h["start"]] + new_tag + html[h["tag_end"]:]

    # 3) 生成目录导航
    nav_links = "\n".join(
        f'    <a href="#{h["id"]}">{h["label"]}</a>' for h in headings
    )
    toc_html = (
        '<aside class="doc-toc" id="doc-toc">\n'
        '  <div class="doc-toc-head">\n'
        '    <span class="doc-toc-title">📑 本文章节</span>\n'
        '    <button class="doc-toc-hide" id="doc-toc-hide" type="button" title="收起目录">✕</button>\n'
        '  </div>\n'
        '  <nav class="doc-toc-nav">\n'
        f'{nav_links}\n'
        '  </nav>\n'
        '</aside>'
    )
    layout_open = (
        '<div class="doc-layout">\n'
        '  <button class="doc-toc-show" id="doc-toc-show" type="button">📑 目录</button>\n'
        f'  {toc_html}\n'
        '  <main class="doc-main">\n'
    )
    layout_close = "\n  </main>\n</div>\n"

    # 4) 注入样式到 head（必须用 <style> 包裹，否则不会生效）
    style_block = "<style>\n" + TOC_CSS + "</style>\n"
    head_end = html.lower().find("</head>")
    if head_end != -1:
        html = html[:head_end] + style_block + html[head_end:]
    else:
        html = style_block + html

    # 5) 包裹 body 内容 + 注入脚本
    body_open = re.search(r"<body[^>]*>", html, re.IGNORECASE)
    body_close = html.rfind("</body>")
    if body_open and body_close != -1:
        content_start = body_open.end()
        html = (
            html[:content_start]
            + "\n" + layout_open
            + html[content_start:body_close]
            + layout_close + TOC_JS
            + html[body_close:]
        )
    else:
        # 没有 body 标签：整体包裹
        html = (
            "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
            + TOC_CSS
            + "\n</head>\n<body>\n" + layout_open + html + layout_close
            + TOC_JS + "\n</body>\n</html>\n"
        )

    path.write_text(html, encoding="utf-8")
    print(f"  [完成] {path.name}: 注入 {len(headings)} 个章节导航")
    return True


def main() -> None:
    targets = sorted(DOCS_ROOT.glob("**/articles/*.html"))
    if not targets:
        print("未找到任何文章 HTML 文件")
        return
    print(f"共发现 {len(targets)} 个文章文件")
    changed = 0
    for p in targets:
        if process_file(p):
            changed += 1
    print(f"\n处理完成: {changed} 个文件已更新")


if __name__ == "__main__":
    main()
