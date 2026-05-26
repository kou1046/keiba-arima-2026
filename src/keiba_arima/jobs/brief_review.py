"""直近に行われた重賞の review を生成する (日曜深夜、結果が出揃った頃)。

過去 3 日以内に走った重賞を対象に、結果と事前 briefing を突き合わせた review を生成。
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
        race_ids = graded_races_between(con, today - timedelta(days=3), today)
        if not race_ids:
            log.info("no recently-run graded races")
            return
        r2 = R2Client()
        for race_id in race_ids:
            publish_race(con, r2, race_id, is_review=True)
    finally:
        con.close()


def main() -> None:
    run("brief_review", _main)


if __name__ == "__main__":
    main()
