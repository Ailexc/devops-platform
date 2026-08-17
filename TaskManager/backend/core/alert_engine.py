"""
Alert Engine — three-level alerting with notification channels.

Level 1 (Warning):   single task failure → log + dashboard marker
Level 2 (Critical):  retry exhausted / breaker opened / queue backlog → webhook
Level 3 (Recovery):  breaker closed / task recovered → same-channel recovery notice
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERY = "recovery"


@dataclass
class Alert:
    level: AlertLevel
    source: str          # e.g. "IAM全量", "生产-apne1"
    message: str
    detail: str = ""


class AlertEngine:
    """Dispatch alerts to configured channels."""

    def __init__(self):
        self._channels: list[Callable[[Alert], None]] = []

    def register_channel(self, channel_fn: Callable[[Alert], None]):
        """Register a notification channel (log, webhook, etc.)."""
        self._channels.append(channel_fn)

    def emit(self, alert: Alert):
        logger.info(f"[{alert.level.value.upper()}] {alert.source}: {alert.message}")
        for channel in self._channels:
            try:
                channel(alert)
            except Exception as e:
                logger.error(f"Alert channel failed: {e}")

    def warning(self, source: str, message: str, detail: str = ""):
        self.emit(Alert(AlertLevel.WARNING, source, message, detail))

    def critical(self, source: str, message: str, detail: str = ""):
        self.emit(Alert(AlertLevel.CRITICAL, source, message, detail))

    def recovery(self, source: str, message: str, detail: str = ""):
        self.emit(Alert(AlertLevel.RECOVERY, source, message, detail))


# ── Built-in channels ───────────────────────────────────────────────


def log_channel(alert: Alert):
    """Default channel: log at appropriate level."""
    level_map = {
        AlertLevel.WARNING: logger.warning,
        AlertLevel.CRITICAL: logger.error,
        AlertLevel.RECOVERY: logger.info,
    }
    level_map[alert.level](f"[{alert.source}] {alert.message} | {alert.detail}")
