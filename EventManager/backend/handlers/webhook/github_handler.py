import asyncio
import logging
import random

from apps.event_store.models import Event
from core.handler import BaseEventHandler, HandlerResult

logger = logging.getLogger(__name__)


class GitHubWebhookHandler(BaseEventHandler):
    """GitHub Webhook 事件"""

    event_type_pattern = "webhook.github.*"

    display = {
        "events": [
            {"type": "webhook.github.push", "desc": "代码推送"},
            {"type": "webhook.github.pull_request", "desc": "PR 打开/合并/关闭"},
            {"type": "webhook.github.issues", "desc": "Issue 创建/关闭"},
            {"type": "webhook.github.release", "desc": "Release 发布"},
            {"type": "webhook.github.star", "desc": "收藏/点赞"},
        ],
        "schema": {
            "github_event": {"type": "string", "required": True, "desc": "GitHub 事件类型", "example": "push"},
            "repository": {"type": "string", "required": True, "desc": "仓库全名", "example": "my-org/my-repo"},
            "ref": {"type": "string", "required": False, "default": "main", "desc": "分支/标签引用", "example": "feature/new-api"},
            "commits": {"type": "integer", "required": False, "desc": "提交数量", "example": 3},
        },
        "example": {
            "github_event": "push",
            "repository": "my-org/my-repo",
            "ref": "main",
            "commits": 3,
        },
    }

    async def handle(self, event: Event) -> HandlerResult:
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)

        gh_event = event.raw_payload.get("github_event", "push")
        repo = event.raw_payload.get("repository", "unknown/repo")
        ref = event.raw_payload.get("ref", "main")

        logger.info("GitHub %s %s (%s) processed in %.2fs", gh_event, repo, ref, delay)
        return HandlerResult(
            success=True,
            message=f"GitHub {gh_event} on {repo}/{ref}",
            data={
                "service": "github",
                "event": gh_event,
                "repository": repo,
                "ref": ref,
                "commits": event.raw_payload.get("commits", 1),
                "processed_delay": round(delay, 2),
            },
        )
