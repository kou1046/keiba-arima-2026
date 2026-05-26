"""過去 15 年の重賞 (G1/G2/G3) を全競馬場ぶん取得する (workflow_dispatch、最長 ~3h)。

開催日単位で全 race_id を列挙し、fetch 後に grade を持つレースだけ保存する。
grade なし (平場) も「取得済」として state に残し、resume 時の再 fetch を防ぐ。
"""

from __future__ import annotations

from .. import config
from ..clients.netkeiba import NetkeibaClient, RacePage
from ..discover import weekend_dates
from . import run
from ._scrape import collect_ids_on_dates, scrape_ids


def _is_graded(page: RacePage) -> bool:
    return page.race.grade is not None


def _main() -> None:
    client = NetkeibaClient()
    try:
        ids = collect_ids_on_dates(client, weekend_dates(config.SCOPE.stakes_years))
        scrape_ids(client, ids, keep=_is_graded)
    finally:
        client.close()


def main() -> None:
    run("backfill_stakes", _main)


if __name__ == "__main__":
    main()
