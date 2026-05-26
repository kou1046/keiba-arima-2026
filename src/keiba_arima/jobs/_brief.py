"""brief 系 job の共通処理: viz → LLM briefing/review → R2 upload → index 更新。"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

from .. import briefing, config, publish, viz
from ..clients.r2 import R2Client

log = logging.getLogger(__name__)


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def graded_races_between(con, start: date, end: date) -> list[str]:
    rows = con.execute(
        "SELECT race_id FROM races WHERE grade IS NOT NULL "
        "AND race_date BETWEEN ? AND ? ORDER BY race_date",
        [start, end],
    ).fetchall()
    return [r[0] for r in rows]


def publish_race(con, r2: R2Client, race_id: str, is_review: bool, weather_note: str = "") -> str:
    ts = _ts()
    charts = viz.render_all(con, race_id)
    chart_urls = publish.upload_charts(r2, race_id, ts, charts)
    if is_review:
        prior = _latest_briefing_markdown(r2, race_id)
        markdown = briefing.generate_review(con, race_id, prior, chart_urls)
    else:
        note = "\n".join(n for n in (weather_note, _baba_note(con, race_id)) if n)
        markdown = briefing.generate_briefing(con, race_id, chart_urls, note)
    key, url = publish.upload_briefing(r2, race_id, ts, markdown, is_review)
    publish.update_index(
        r2,
        {
            "race_id": race_id,
            "type": "review" if is_review else "briefing",
            "key": key,
            "url": url,
            "generated_at": ts,
        },
    )
    log.info("published %s briefing: %s", "review" if is_review else "pre-race", url)
    return url


def _baba_note(con, race_id: str) -> str:
    """そのレースの競馬場の最新 JRA 馬場情報を 1 行で。baba 未蓄積なら空 (best-effort)。"""
    try:
        row = con.execute(
            "SELECT b.cushion_value, b.turf_moisture, b.dirt_moisture, b.measured_date "
            "FROM baba b JOIN races r ON r.race_id = ? AND b.course = r.course "
            "ORDER BY b.measured_date DESC LIMIT 1",
            [race_id],
        ).fetchone()
    except Exception as e:  # noqa: BLE001 - baba view 不在 / 取得失敗は無視
        log.warning("baba note unavailable: %s", e)
        return ""
    if not row:
        return ""
    cushion, turf, dirt, mdate = row
    return (
        f"JRA 馬場 ({mdate}): クッション値={cushion or '-'} "
        f"含水率 芝={turf or '-'}% ダート={dirt or '-'}%"
    )


def _latest_briefing_markdown(r2: R2Client, race_id: str) -> str:
    raw = r2.get_text(config.R2_INDEX_KEY)
    if not raw:
        return ""
    entries = [
        b
        for b in json.loads(raw).get("briefings", [])
        if b.get("race_id") == race_id and b.get("type") == "briefing"
    ]
    if not entries:
        return ""
    entries.sort(key=lambda b: b.get("generated_at", ""), reverse=True)
    return r2.get_text(entries[0]["key"]) or ""
