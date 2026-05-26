"""過去 15 年の JRA 重賞 (G1/G2/G3) を取得する (workflow_dispatch)。

開催日の list ページで重賞だけ pre-filter してから fetch する (全レースを取りに行かない)。
discovery (list) と fetch の双方が state で resume 可能。grade は list テキスト由来なので
detail 取得後に grade None だった場合の保険として keep でも再チェックする。
"""

from __future__ import annotations

from .. import config
from ..clients.netkeiba import NetkeibaClient, RacePage
from ..discover import weekend_dates
from . import run
from ._scrape import discover_graded_stakes, scrape_ids


def _is_graded(page: RacePage) -> bool:
    return page.race.grade is not None


def _main() -> None:
    client = NetkeibaClient()
    try:
        candidates = discover_graded_stakes(client, weekend_dates(config.SCOPE.stakes_years))
        scrape_ids(client, candidates, keep=_is_graded)
    finally:
        client.close()


def main() -> None:
    run("backfill_stakes", _main)


if __name__ == "__main__":
    main()
