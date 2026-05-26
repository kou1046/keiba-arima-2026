"""job entrypoint 群 (設計書の jobs/)。各 module は薄い orchestration で、
処理本体は store / briefing / publish / clients に委譲する。

run() は全 job 共通の外枠: ロギング設定 + 例外時に LINE 通知して re-raise
(GH Actions の step も赤くして気付けるように)。
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from ..clients import line


def run(name: str, fn: Callable[[], None]) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    log = logging.getLogger(name)
    try:
        fn()
        log.info("done")
    except Exception as e:  # noqa: BLE001 - 通知して必ず再送出
        log.exception("job failed")
        line.notify(f"[keiba-arima] {name} 失敗ワン⚠️ {type(e).__name__}: {e}")
        raise
