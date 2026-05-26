"""JRA 馬場情報 (クッション値 / 含水率) を当日 fetch して蓄積する (開催日 cron)。"""

from __future__ import annotations

import logging

from .. import store
from ..clients.jra import JRAClient
from . import run

log = logging.getLogger(__name__)


def _main() -> None:
    client = JRAClient()
    try:
        conditions = client.fetch_baba()
        store.upsert_baba(conditions)
        log.info("baba: stored %d course rows", len(conditions))
    finally:
        client.close()


def main() -> None:
    run("fetch_baba", _main)


if __name__ == "__main__":
    main()
