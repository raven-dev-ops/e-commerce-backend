import logging
from typing import Any

import requests


class SlackWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str, timeout: int = 5) -> None:
        super().__init__()
        self.webhook_url = webhook_url
        self.timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        if not self.webhook_url:
            return
        try:
            message = self.format(record)
            payload: dict[str, Any] = {"text": message}
            requests.post(self.webhook_url, json=payload, timeout=self.timeout)
        except Exception:
            self.handleError(record)
