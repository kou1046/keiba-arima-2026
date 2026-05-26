"""直近の週末に開催された全レースを取得する (日曜 23:00 JST cron)。"""

from __future__ import annotations

from ..clients.netkeiba import NetkeibaClient
from ..discover import recent_weekend_dates
from . import run
from ._scrape import collect_ids_on_dates, scrape_ids


def _main() -> None:
    client = NetkeibaClient()
    try:
        ids = collect_ids_on_dates(client, recent_weekend_dates())
        scrape_ids(client, ids)
    finally:
        client.close()


def main() -> None:
    run("scrape_weekly", _main)


if __name__ == "__main__":
    main()
