"""対象レース (config.TARGET_RACE_NAMES、既定: 有馬記念) の出走馬と、各馬のその開催年の
全走行記録を取得する (友人提案)。

backfill_horses は「今日から数年」窓なので過去年 (例 2015 有馬記念) の出走馬の同年成績を
拾えない。この job は対象レースの開催年に固定して、その馬のその年のキャンペーンを埋める。
前提: 対象レース (有馬記念=G1) の results が既に取得済 (backfill_stakes 後)。
"""

from __future__ import annotations

import logging

from .. import config, db, state, store
from ..clients.netkeiba import NetkeibaClient
from . import run
from ._scrape import scrape_ids

log = logging.getLogger(__name__)


def _target_runners() -> list[tuple[int, list[str]]]:
    """対象レースごとに (開催年, 出走馬 horse_id リスト) を DB から収集する。"""
    con = db.connect()
    try:
        like = " OR ".join(["name LIKE ?"] * len(config.TARGET_RACE_NAMES))
        args = [f"%{n}%" for n in config.TARGET_RACE_NAMES]
        races = con.execute(
            f"SELECT race_id, race_date FROM races WHERE {like} ORDER BY race_date",
            args,
        ).fetchall()
        out: list[tuple[int, list[str]]] = []
        for race_id, race_date in races:
            runners = [
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT horse_id FROM results WHERE race_id = ? AND horse_id <> ''",
                    [race_id],
                ).fetchall()
            ]
            out.append((race_date.year, runners))
        return out
    finally:
        con.close()


def _main() -> None:
    plan = _target_runners()
    if not plan:
        log.info("no target races in db yet (run backfill_stakes first)")
        return
    log.info("target races: %d", len(plan))
    client = NetkeibaClient()
    try:
        for year, runners in plan:
            for horse_id in runners:
                if horse_id not in state.scraped_horses():
                    store.upsert_horses([client.fetch_horse(horse_id)])
                    state.mark_horses([horse_id])
                # その馬の「対象レース開催年」の全レースを取得 (scrape_ids が race 単位で dedup)
                scrape_ids(client, client.list_horse_race_ids_in_year(horse_id, year))
    finally:
        client.close()


def main() -> None:
    run("backfill_target_runners", _main)


if __name__ == "__main__":
    main()
