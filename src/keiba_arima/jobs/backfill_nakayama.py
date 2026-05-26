"""過去 10 年の中山 2500m を平場含め全て取得する (workflow_dispatch、~2h)。

中山は race_id の競馬場コード '06'。fetch 前に id で前置フィルタして無駄打ちを減らし、
fetch 後に距離 2500m で keep する。
"""

from __future__ import annotations

from .. import config
from ..clients.netkeiba import NetkeibaClient, RacePage
from ..discover import weekend_dates
from . import run
from ._scrape import collect_ids_on_dates, scrape_ids

_NAKAYAMA_COURSE_CODE = "06"


def _is_nakayama_2500(page: RacePage) -> bool:
    return page.race.course == "中山" and page.race.distance_m == 2500


def _main() -> None:
    client = NetkeibaClient()
    try:
        ids = collect_ids_on_dates(client, weekend_dates(config.SCOPE.nakayama_2500_years))
        nakayama_ids = [i for i in ids if i[4:6] == _NAKAYAMA_COURSE_CODE]
        scrape_ids(client, nakayama_ids, keep=_is_nakayama_2500)
    finally:
        client.close()


def main() -> None:
    run("backfill_nakayama", _main)


if __name__ == "__main__":
    main()
