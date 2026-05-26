"""重賞・中山 backfill で集まった出走馬の profile と直近 3 年の戦績を取得する。

backfill-stakes / backfill-nakayama 完了後に走らせる前提 (最長 ~5-6h)。
results に登場する horse_id を集め、未取得の馬ごとに profile + その馬の直近レースを取得。
"""

from __future__ import annotations

from datetime import date, timedelta

from .. import config, db, state, store
from ..clients.netkeiba import NetkeibaClient
from . import run
from ._scrape import scrape_ids


def _distinct_horse_ids() -> list[str]:
    con = db.connect()
    try:
        rows = con.execute("SELECT DISTINCT horse_id FROM results WHERE horse_id <> ''").fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def _main() -> None:
    since = date.today() - timedelta(days=365 * config.SCOPE.horse_history_years)
    client = NetkeibaClient()
    try:
        for horse_id in state.pending_horses(_distinct_horse_ids()):
            store.upsert_horses([client.fetch_horse(horse_id)])
            past_ids = client.list_horse_race_ids(horse_id, since)
            scrape_ids(client, past_ids)
            state.mark_horses([horse_id])
    finally:
        client.close()


def main() -> None:
    run("backfill_horses", _main)


if __name__ == "__main__":
    main()
