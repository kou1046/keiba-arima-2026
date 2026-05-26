"""JRA 馬場情報 (クッション値 / 含水率) の取得。memory id 1623 の第2弾。

開催当日に fetch して蓄積する運用。netkeiba ほど神経質でなくてよいが、JRA も過度な
polling は避け 1 日数回程度に留める前提。parse は parsers/baba (純粋関数) に委譲。
"""

from __future__ import annotations

from datetime import date

import httpx

from .. import config
from ..models import BabaCondition
from ..parsers import baba as baba_parser


def merge_conditions(
    cushion_html: str, moisture_html: str, measured_date: date
) -> list[BabaCondition]:
    """2 ページの parse 結果を競馬場ごとに 1 行へマージする (純粋関数、テスト用)。"""
    cushion = baba_parser.parse_cushion(cushion_html)
    moisture = baba_parser.parse_moisture(moisture_html)
    courses = set(cushion) | set(moisture)
    out: list[BabaCondition] = []
    for course in config.JRA_COURSES:
        if course not in courses:
            continue
        turf, dirt = moisture.get(course, (None, None))
        out.append(
            BabaCondition(
                course=course,
                measured_date=measured_date,
                cushion_value=cushion.get(course),
                turf_moisture=turf,
                dirt_moisture=dirt,
            )
        )
    return out


class JRAClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": config.USER_AGENT}, timeout=httpx.Timeout(20.0)
        )

    def close(self) -> None:
        self._client.close()

    def fetch_baba(self, measured_date: date | None = None) -> list[BabaCondition]:
        measured_date = measured_date or date.today()
        cushion = self._client.get(config.JRA_CUSHION_URL)
        cushion.raise_for_status()
        moisture = self._client.get(config.JRA_MOISTURE_URL)
        moisture.raise_for_status()
        return merge_conditions(cushion.text, moisture.text, measured_date)
