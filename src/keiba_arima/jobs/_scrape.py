"""scrape 系 job の共通処理。resume を効かせるため id 単位で state を更新する。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from .. import state, store
from ..clients import line
from ..clients.netkeiba import NetkeibaClient, RacePage
from ..parsers import ParseError

log = logging.getLogger(__name__)


def scrape_ids(
    client: NetkeibaClient, race_ids: list[str], keep: Callable[[RacePage], bool] | None = None
) -> int:
    """未取得の race_id を順に fetch → (keep を満たせば) 保存。保存件数を返す。

    1 レースの ParseError では job 全体を止めず、parse_errors.json に積んで続行する
    (DOM 変更で週次データに穴を空けないため)。PermanentBlockError (403) は伝播させ abort。
    """
    pending = state.pending_races(race_ids)
    log.info("scrape: %d candidates, %d pending", len(race_ids), len(pending))
    saved = 0
    errors: list[tuple[str, str]] = []
    for rid in pending:
        try:
            page = client.fetch_race(rid)
        except ParseError as e:
            log.warning("parse failed, skipping %s: %s", rid, e)
            errors.append((rid, str(e)))
            state.mark_races([rid])  # 再取得ループを避けるため済み扱い
            continue
        if keep is None or keep(page):
            store.upsert_race_page(page)
            saved += 1
        state.mark_races([rid])  # 採否に関わらず再取得しないよう記録
    if errors:
        state.append_parse_errors(errors)
        line.notify(f"[keiba-arima] parse 失敗 {len(errors)} 件ワン⚠️ (job は続行、parse_errors.json 参照)")
    log.info("scrape: saved %d, parse_errors %d", saved, len(errors))
    return saved


def collect_ids_on_dates(client: NetkeibaClient, dates: list[date]) -> list[str]:
    ids: list[str] = []
    for d in dates:
        ids.extend(client.list_race_ids_on(d))
    return ids


def discover_graded_stakes(client: NetkeibaClient, dates: list[date]) -> list[str]:
    """各日の list ページから JRA 重賞だけを抽出して候補集合に蓄積する (resume 可能)。

    list 済の日付は state に記録し、再 dispatch では list を再取得しない (~1,560 list req を
    一度きりに)。fetch 自体は呼び出し側 (scrape_ids) が候補に対して行う。
    """
    pending_dates = [d for d in dates if d.strftime("%Y%m%d") not in state.listed_dates()]
    log.info("discover: %d dates total, %d to list", len(dates), len(pending_dates))
    for d in pending_dates:
        state.add_stakes_candidates(client.list_graded_race_ids_on(d))
        state.mark_listed_dates([d.strftime("%Y%m%d")])
    return sorted(state.stakes_candidates())
