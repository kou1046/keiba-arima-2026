"""rate-limited httpx session。netkeiba へのアクセスは必ずこれ経由。

ポリシー (config.py): 8s 固定 + jitter、並列なし、403/429/5xx は exponential backoff、
MAX_RETRIES 失敗で例外を上げて呼び出し側 (job) が abort する。
"""

from __future__ import annotations

import logging
import random
import time

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from . import config

logger = logging.getLogger(__name__)

# netkeiba は EUC-JP。httpx は charset 推定が弱いので明示する。
NETKEIBA_ENCODING = "euc-jp"


class RateLimitedError(Exception):
    """403 / 429 を retry 対象として包む。"""


class RateLimitedClient:
    """1 process 1 インスタンス想定。close() で session を畳む。"""

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": config.USER_AGENT},
            timeout=httpx.Timeout(20.0),
            follow_redirects=True,
        )
        self._last_request_at = 0.0

    def __enter__(self) -> "RateLimitedClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = config.REQUEST_INTERVAL_S + random.uniform(0, config.REQUEST_JITTER_S) - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    @retry(
        retry=retry_if_exception_type((RateLimitedError, httpx.TransportError)),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(config.MAX_RETRIES),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def get_html(self, url: str) -> str:
        """netkeiba ページを取得して EUC-JP デコード済の HTML を返す。"""
        self._throttle()
        resp = self._client.get(url)
        if resp.status_code in (403, 429):
            raise RateLimitedError(f"{resp.status_code} for {url}")
        resp.raise_for_status()
        resp.encoding = NETKEIBA_ENCODING
        return resp.text
