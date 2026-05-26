"""scrape 系 job の共通処理。resume を効かせるため id 単位で state を更新する。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from .. import state, store
from ..clients.netkeiba import NetkeibaClient, RacePage

log = logging.getLogger(__name__)


def scrape_ids(
    client: NetkeibaClient, race_ids: list[str], keep: Callable[[RacePage], bool] | None = None
) -> int:
    """未取得の race_id を順に fetch → (keep を満たせば) 保存。保存件数を返す。"""
    pending = state.pending_races(race_ids)
    log.info("scrape: %d candidates, %d pending", len(race_ids), len(pending))
    saved = 0
    for rid in pending:
        page = client.fetch_race(rid)
        if keep is None or keep(page):
            store.upsert_race_page(page)
            saved += 1
        state.mark_races([rid])  # 採否に関わらず再取得しないよう記録
    log.info("scrape: saved %d", saved)
    return saved


def collect_ids_on_dates(client: NetkeibaClient, dates: list[date]) -> list[str]:
    ids: list[str] = []
    for d in dates:
        ids.extend(client.list_race_ids_on(d))
    return ids
