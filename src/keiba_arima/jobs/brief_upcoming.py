"""14 日以内に行われる重賞の事前 briefing を生成する (日曜 23:30 / 木曜 21:00 JST)。

DB に入っている (= 出走表/枠順を scrape 済の) 重賞を対象に briefing を生成。
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from .. import db
from ..clients.r2 import R2Client
from . import run
from ._brief import graded_races_between, publish_race

log = logging.getLogger(__name__)


def _main() -> None:
    today = date.today()
    con = db.connect()
    try:
        race_ids = graded_races_between(con, today, today + timedelta(days=14))
        if not race_ids:
            log.info("no upcoming graded races in window")
            return
        r2 = R2Client()
        for race_id in race_ids:
            publish_race(con, r2, race_id, is_review=False)
    finally:
        con.close()


def main() -> None:
    run("brief_upcoming", _main)


if __name__ == "__main__":
    main()
