"""
Real Celery test tasks — genuine IO operations for demo validation.

These tasks perform actual work:
  1. network_collect: fetch data from public API, write to local file
  2. data_quality_check: read demo store, validate integrity, write report
"""

import json
import os
import time
import urllib.request
from datetime import datetime

from celery import shared_task

OUTPUT_DIR = "/tmp/cmdb_test"


def _ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _update_history(task_id, result_data):
    """Update the history record when a Celery task completes."""
    from datetime import datetime
    from api.history.models import ExecutionRecord

    try:
        record = ExecutionRecord.objects.get(celery_task_id=task_id)
    except ExecutionRecord.DoesNotExist:
        return

    record.status = result_data.get("status", "success")
    record.duration = result_data.get("duration", "-")
    record.detail = result_data.get("summary", "")
    record.result = result_data
    record.finished_at = datetime.now()
    if result_data.get("status") == "failed":
        record.error = result_data.get("error", "未知错误")
    record.save()


@shared_task(bind=True)
def network_collect(self):
    """Fetch users from jsonplaceholder API, save to local JSON file.

    Real operations: HTTP GET → parse → write file → return stats.
    """
    from core.result_builder import ResultBuilder

    _ensure_dir()
    task_id = self.request.id
    builder = ResultBuilder()

    url = "https://jsonplaceholder.typicode.com/users"
    builder.log("📡 Phase 1: 请求 jsonplaceholder API")
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        result = builder.fail(str(e)).build("网络采集失败", extra={"url": url})
        _update_history(task_id, result)
        return result
    builder.log(f"  ✅ 获取 {len(data)} 条用户数据")

    # Enrich each record with sync metadata
    builder.log("🧹 Phase 2: 数据清洗（字段裁剪 + 补全同步元数据）")
    enriched = []
    for user in data:
        enriched.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "company": user["company"]["name"],
            "city": user["address"]["city"],
            "synced_at": datetime.now().isoformat(),
        })

    # Write to file
    filename = f"sync_{task_id[:8]}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    builder.log("💾 Phase 3: 批量写入本地 JSON 文件")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": task_id,
            "source": url,
            "count": len(enriched),
            "records": enriched,
        }, f, ensure_ascii=False, indent=2)
    builder.log(f"  ✅ 写入完成: {filename}")

    builder.add_stat("count", "采集数量", len(enriched), "条")
    builder.add_artifact(filepath, "json")
    result = builder.build(f"采集 {len(enriched)} 条用户数据，写入 {filename}")
    _update_history(task_id, result)
    return result


@shared_task(bind=True)
def data_quality_check(self):
    """Read demo store data, validate integrity, write Markdown report.

    Real operations: read data → validate → write .md report file.
    """
    from core.result_builder import ResultBuilder

    _ensure_dir()
    task_id = self.request.id
    builder = ResultBuilder()

    # 真实任务树（配置层 + 能力层 + 调度层三源合并）
    from core.task_tree_service import build_task_tree
    from api.history.models import ExecutionRecord

    builder.log("📖 读取 CMDB 任务树（三源合并）")
    accounts = build_task_tree().get("accounts", [])
    history = list(ExecutionRecord.objects.values("task_name", "module", "status"))

    # Validation logic
    checks = []
    total_resources = 0
    total_regions = 0
    issues = 0

    builder.log("🔍 Phase 1: 检查各账号/区域的资源组配置")
    for acct in accounts:
        acct_name = acct.get("name", "unknown")
        regions = acct.get("regions", [])
        total_regions += len(regions)

        for reg in regions:
            reg_code = reg.get("code", "unknown")
            groups = reg.get("resource_groups", [])
            for grp in groups:
                res_list = grp.get("resources", [])
                total_resources += len(res_list)
                # Check: empty resource group
                if not res_list:
                    checks.append(f"- ⚠️ [{acct_name}/{reg_code}] 分组「{grp.get('name', '?')}」无资源类型")
                    issues += 1
                else:
                    checks.append(f"- ✅ [{acct_name}/{reg_code}] {grp.get('name', '?')}: {len(res_list)} 个资源类型")

            # Check: no configured regions
            if not groups:
                checks.append(f"- ⚠️ [{acct_name}/{reg_code}] 未配置任何资源组")
                issues += 1
    builder.log(f"  ✅ 检查完成: 共 {total_regions} 区域 · {total_resources} 资源类型")

    # Check history records
    builder.log("📜 Phase 2: 检查执行历史")
    failed_records = [r for r in history if r.get("status") == "failed"]
    if failed_records:
        checks.append(f"- ⚠️ 历史记录中有 {len(failed_records)} 条失败任务")
        issues += len(failed_records)
    else:
        checks.append(f"- ✅ 历史记录无失败任务 ({len(history)} 条全部成功)")
    builder.log(f"  ✅ 历史记录: {len(history)} 条, 失败 {len(failed_records)} 条")

    # Summary
    accounts_count = len(accounts)
    passed = len(checks) - issues

    # Build Markdown report
    builder.log("📄 Phase 3: 生成 Markdown 质检报告")
    report = f"""# CMDB 数据质检报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**任务ID**: {task_id}

## 📊 概览

| 指标 | 数值 |
|------|------|
| 账号数 | {accounts_count} |
| 区域数 | {total_regions} |
| 资源类型总数 | {total_resources} |
| 检查项 | {len(checks)} |
| 通过 | {passed} |
| 异常 | {issues} |

## 📋 检查详情

{chr(10).join(checks)}

## 📈 最近任务记录

| ID | 任务 | 状态 | 耗时 |
|----|------|------|------|
"""
    for r in history[:10]:
        report += f"| {r.get('id', '-')} | {r.get('task', '-')} | {r.get('status', '-')} | {r.get('duration', '-')} |\n"

    # Write report file
    filename = f"check_{task_id[:8]}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    builder.log(f"  ✅ 报告已写入 {filename}")

    builder.add_stats([
        {"key": "accounts", "label": "账号数", "value": accounts_count, "unit": "个"},
        {"key": "regions", "label": "区域数", "value": total_regions, "unit": "个"},
        {"key": "resources", "label": "资源类型", "value": total_resources, "unit": "类"},
        {"key": "checks", "label": "检查项", "value": len(checks), "unit": "项"},
        {"key": "passed", "label": "通过", "value": passed, "unit": "项"},
        {"key": "issues", "label": "异常", "value": issues, "unit": "项"},
    ])
    builder.add_artifact(filepath, "md")
    result = builder.build(
        f"检查 {accounts_count} 账号 · {total_regions} 区域 · {total_resources} 资源类型，{passed} 通过 / {issues} 异常"
    )
    _update_history(task_id, result)
    return result


# ═══════════════════════════════════════════════════════════════════
# Task 3: Open Library 图书数据采集与分析 Pipeline
# ═══════════════════════════════════════════════════════════════════

import statistics as _stats
from collections import Counter as _Counter
from urllib.parse import quote as _quote


_OPENLIB_TOPICS = [
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("machine learning", "Machine Learning"),
    ("science fiction", "Science Fiction"),
    ("history", "History"),
]


def _ol_fetch(url, retries=3, timeout=15):
    """Fetch URL with retries and rate-limit respect."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CMDB-Demo/1.0 (demo@example.com)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))  # linear backoff
            else:
                raise


@shared_task(bind=True)
def openlibrary_collect(self):
    """Open Library 图书数据采集与分析 Pipeline.

    Phase 1: 从 Open Library Search API 采集 5 个主题的图书数据
    Phase 2: 数据清洗（去重、补全、标准化）
    Phase 3: 多维分析（主题分布、年代趋势、作者排行等）
    Phase 4: 生成 Markdown 报告 + JSON 数据文件
    """
    from core.result_builder import ResultBuilder

    _ensure_dir()
    task_id = self.request.id
    builder = ResultBuilder()
    start = time.time()  # 中间分析代码仍使用 start 计算阶段耗时

    def _log(msg):
        builder.log(msg)

    # ── Phase 1: 采集 ──────────────────────────────────────────
    _log("📡 Phase 1: 开始采集图书数据")
    all_books = []
    topic_counts = {}
    fetch_errors = []

    for query, label in _OPENLIB_TOPICS:
        _log(f"📡 采集主题「{label}」(query={query})...")
        topic_books = []
        for page in range(1, 4):  # 3 pages × 100 = 300 per topic
            url = (
                f"https://openlibrary.org/search.json"
                f"?q={_quote(query)}&limit=100&page={page}"
                f"&fields=key,title,author_name,first_publish_year,"
                f"edition_count,has_fulltext,public_scan_b,cover_i"
            )
            try:
                data = _ol_fetch(url)
                docs = data.get("docs", [])
                for doc in docs:
                    topic_books.append({
                        "key": doc.get("key", ""),
                        "title": doc.get("title", "Unknown"),
                        "authors": doc.get("author_name", []),
                        "first_publish_year": doc.get("first_publish_year"),
                        "edition_count": doc.get("edition_count", 0),
                        "has_fulltext": doc.get("has_fulltext", False),
                        "is_public": doc.get("public_scan_b", False),
                        "cover_id": doc.get("cover_i"),
                        "topic": label,
                    })
                _log(f"  ✅ page {page}/3: 获取 {len(docs)} 条")
                time.sleep(0.4)  # respect rate limit
            except Exception as e:
                err_msg = str(e)[:80]
                _log(f"  ❌ page {page}/3: 请求失败 — {err_msg}")
                fetch_errors.append(f"{label} page {page}: {err_msg}")
                time.sleep(1)

        topic_counts[label] = len(topic_books)
        all_books.extend(topic_books)
        _log(f"  📊 {label} 采集完成: {len(topic_books)} 条")

    _log(f"📡 Phase 1 完成: 共采集 {len(all_books)} 条原始数据")

    if not all_books:
        _log("❌ 所有数据源请求失败，任务终止")
        result = builder.fail("所有数据源请求失败: " + "; ".join(fetch_errors[:3])).build("Open Library 采集失败")
        _update_history(task_id, result)
        return result

    # ── Phase 2: 清洗 ──────────────────────────────────────────
    _log("🧹 Phase 2: 开始数据清洗")
    # 去重: 按 key
    seen_keys = set()
    unique_books = []
    duplicates = 0
    for book in all_books:
        k = book["key"]
        if k and k not in seen_keys:
            seen_keys.add(k)
            unique_books.append(book)
        else:
            duplicates += 1
    _log(f"  🔄 去重完成: {len(all_books)} → {len(unique_books)} (去除 {duplicates} 重复)")

    # 补全 & 标准化
    null_authors = 0
    for book in unique_books:
        if not book["authors"]:
            book["authors"] = ["Unknown"]
            null_authors += 1
        # 标准化出版年份
        y = book["first_publish_year"]
        if y and (y < 1000 or y > 2100):
            book["first_publish_year"] = None
    _log(f"  ✏️ 补全完成: {null_authors} 条缺失作者已标记为 Unknown")

    # 按年代分桶
    def _decade(y):
        if not y:
            return "Unknown"
        return f"{(y // 10) * 10}s"

    for book in unique_books:
        book["decade"] = _decade(book["first_publish_year"])
    _log(f"  📅 年代分桶完成")

    # ── Phase 3: 分析 ──────────────────────────────────────────
    _log("📊 Phase 3: 开始数据分析")

    # 1. 主题分布
    topic_dist = _Counter(b["topic"] for b in unique_books)
    _log(f"  📂 主题分布: {dict(topic_dist)}")

    # 2. 年代分布
    decade_dist = _Counter(b["decade"] for b in unique_books)
    decade_sorted = sorted(
        [(d, c) for d, c in decade_dist.items() if d != "Unknown"],
        key=lambda x: x[0],
    )
    _log(f"  📅 年代分布: {len(decade_sorted)} 个年代段")

    # 3. Top 10 作者
    author_counter = _Counter()
    for book in unique_books:
        for a in book["authors"][:3]:  # 取前 3 作者
            if a != "Unknown":
                author_counter[a] += 1
    top_authors = author_counter.most_common(10)
    _log(f"  ✍️ Top 作者: {top_authors[0][0]} ({top_authors[0][1]} 本)" if top_authors else "  ✍️ 无作者数据")

    # 4. 版本数统计
    edition_counts = [b["edition_count"] for b in unique_books if b["edition_count"]]
    edition_stats = {}
    if edition_counts:
        edition_stats = {
            "mean": round(_stats.mean(edition_counts), 1),
            "median": _stats.median(edition_counts),
            "max": max(edition_counts),
            "total": sum(edition_counts),
        }
    _log(f"  📖 版本统计: 平均 {edition_stats.get('mean', '-')} 版, 最多 {edition_stats.get('max', '-')} 版")

    # 5. 全文可用率
    fulltext_count = sum(1 for b in unique_books if b["has_fulltext"])
    public_count = sum(1 for b in unique_books if b["is_public"])
    _log(f"  🔓 全文可用: {fulltext_count}/{len(unique_books)} ({round(fulltext_count/len(unique_books)*100, 1)}%)")

    # 6. 跨主题重叠 (同一本书出现在多个搜索结果中 — 在去重前统计)
    key_topics = {}
    for book in all_books:
        k = book["key"]
        if k:
            key_topics.setdefault(k, set()).add(book["topic"])
    cross_topic = {k: v for k, v in key_topics.items() if len(v) > 1}
    _log(f"  🔗 跨主题重叠: {len(cross_topic)} 本")

    # ── Phase 4: 生成报告 ──────────────────────────────────────
    _log("📄 Phase 4: 生成报告")

    duration = f"{time.time() - start:.2f}s"

    # Markdown 报告
    report_lines = [
        f"# 📚 Open Library 图书数据采集与分析报告",
        f"",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**任务ID**: {task_id}",
        f"**耗时**: {duration}",
        f"",
        f"## 📊 采集概览",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 原始采集 | {len(all_books)} 条 |",
        f"| 去重后 | {len(unique_books)} 条 |",
        f"| 重复数 | {duplicates} |",
        f"| 缺失作者 | {null_authors} |",
        f"| 主题数 | {len(topic_counts)} |",
        f"| 请求失败 | {len(fetch_errors)} |",
        f"",
        f"## 📂 主题分布",
        f"",
        f"| 主题 | 采集数 | 去重后 |",
        f"|------|--------|--------|",
    ]
    for query, label in _OPENLIB_TOPICS:
        raw = topic_counts.get(label, 0)
        clean = topic_dist.get(label, 0)
        report_lines.append(f"| {label} | {raw} | {clean} |")

    report_lines += [
        f"",
        f"## 📅 年代分布",
        f"",
        f"| 年代 | 数量 | 占比 |",
        f"|------|------|------|",
    ]
    for decade, count in decade_sorted:
        pct = round(count / len(unique_books) * 100, 1)
        bar = "█" * max(1, int(pct / 3))
        report_lines.append(f"| {decade} | {count} | {pct}% {bar} |")

    report_lines += [
        f"",
        f"## ✍️ Top 10 高产作者",
        f"",
        f"| 排名 | 作者 | 作品数 |",
        f"|------|------|--------|",
    ]
    for i, (author, count) in enumerate(top_authors, 1):
        report_lines.append(f"| {i} | {author} | {count} |")

    report_lines += [
        f"",
        f"## 📖 版本统计",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 平均版本数 | {edition_stats.get('mean', '-')} |",
        f"| 中位数 | {edition_stats.get('median', '-')} |",
        f"| 最多版本 | {edition_stats.get('max', '-')} |",
        f"| 版本总数 | {edition_stats.get('total', '-')} |",
        f"",
        f"## 🔓 开放访问",
        f"",
        f"| 指标 | 数值 | 占比 |",
        f"|------|------|------|",
        f"| 有全文 | {fulltext_count} | {round(fulltext_count/len(unique_books)*100, 1)}% |",
        f"| 公开扫描 | {public_count} | {round(public_count/len(unique_books)*100, 1)}% |",
        f"| 跨主题重叠 | {len(cross_topic)} 本 | - |",
    ]

    if fetch_errors:
        report_lines += [
            f"",
            f"## ⚠️ 请求失败记录",
            f"",
        ]
        for err in fetch_errors[:10]:
            report_lines.append(f"- {err}")

    report = "\n".join(report_lines)

    # 写入文件
    report_filename = f"openlibrary_report_{task_id[:8]}.md"
    report_path = os.path.join(OUTPUT_DIR, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    _log(f"  ✅ 报告已写入 {report_filename}")

    data_filename = f"openlibrary_data_{task_id[:8]}.json"
    data_path = os.path.join(OUTPUT_DIR, data_filename)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": task_id,
            "books": unique_books[:500],  # 控制产物大小
            "stats": {
                "total_raw": len(all_books),
                "total_unique": len(unique_books),
                "duplicates": duplicates,
                "topics": dict(topic_dist),
                "decades": dict(decade_sorted),
                "top_authors": top_authors,
                "edition_stats": edition_stats,
                "fulltext_count": fulltext_count,
                "public_count": public_count,
                "cross_topic_count": len(cross_topic),
            },
        }, f, ensure_ascii=False, indent=2)
    _log(f"  ✅ 数据已写入 {data_filename} ({len(unique_books[:500])} 本书)")
    _log(f"🏁 Phase 4 完成, 总耗时 {duration}")

    # 指标面板
    builder.add_stats([
        {"key": "total_raw", "label": "原始采集", "value": len(all_books), "unit": "条"},
        {"key": "total_unique", "label": "去重后", "value": len(unique_books), "unit": "本"},
        {"key": "duplicates", "label": "重复数", "value": duplicates, "unit": "本"},
        {"key": "fulltext_rate", "label": "全文率", "value": f"{round(fulltext_count/len(unique_books)*100, 1)}%"},
        {"key": "public_rate", "label": "公开扫描", "value": f"{round(public_count/len(unique_books)*100, 1)}%"},
        {"key": "cross_topic", "label": "跨主题重叠", "value": len(cross_topic), "unit": "本"},
        {"key": "fetch_errors", "label": "请求失败", "value": len(fetch_errors), "unit": "次"},
    ])
    # 产物（两个文件都可预览）
    builder.add_artifact(report_path, "md")
    builder.add_artifact(data_path, "json")

    result = builder.build(
        (
            f"采集 {len(all_books)} 条 → 去重 {len(unique_books)} 本 "
            f"({len(topic_counts)} 主题 · {len(decade_sorted)} 个年代) "
            f"| Top 作者: {top_authors[0][0] if top_authors else '-'} "
            f"| 全文率 {round(fulltext_count/len(unique_books)*100, 1)}%"
        ),
        extra={
            "topics": dict(topic_dist),
            "top_authors": [{"name": a, "count": c} for a, c in top_authors[:5]],
            "edition_stats": edition_stats,
        },
    )
    _update_history(task_id, result)
    return result
