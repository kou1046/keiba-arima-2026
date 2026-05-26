"""race-page (db.netkeiba.com/race/<race_id>/) のレースメタを parse。

ページ上部の `diary_snap_cut` / `data_intro` ブロックに
「芝右2500m / 天候:晴 / 馬場:良」等が入る。レース名・グレード・日付は見出しから。
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import Race
from . import ParseError
from ._util import clean, parse_jp_date, to_float, to_int

_SURFACE_RE = re.compile(r"(芝|ダート|ダ|障)")
_DISTANCE_RE = re.compile(r"(\d{3,4})m")
_TURN_RE = re.compile(r"(右|左|直線|障)")
_WEATHER_RE = re.compile(r"天候\s*[:：]\s*(\S+)")
_COND_RE = re.compile(r"(?:馬場|芝|ダート)\s*[:：]\s*(良|稍重|重|不良)")
# netkeiba は重賞をローマ数字 (GI/GII/GIII、環境により全角 GⅠ/GⅡ/GⅢ) で表記する。
# 長いものから先に試して GIII を GI と誤マッチさせない。判定結果は G1/G2/G3 に正規化。
_GRADE_RE = re.compile(r"G\s*(Ⅲ|Ⅱ|Ⅰ|III|II|I|[123])")
_GRADE_NORM = {"Ⅰ": "1", "Ⅱ": "2", "Ⅲ": "3", "I": "1", "II": "2", "III": "3", "1": "1", "2": "2", "3": "3"}


def _grade(text: str) -> str | None:
    m = _GRADE_RE.search(text)
    return f"G{_GRADE_NORM[m.group(1)]}" if m else None


def parse(html: str, race_id: str) -> Race:
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("dl.racedata h1") or soup.select_one(".data_intro h1")
    if title_el is None:
        raise ParseError(f"race title not found: {race_id}")
    name = clean(title_el.get_text())

    intro = soup.select_one(".data_intro") or soup
    meta_text = clean(intro.get_text(" "))

    surface_m = _SURFACE_RE.search(meta_text)
    distance_m = _DISTANCE_RE.search(meta_text)
    if surface_m is None or distance_m is None:
        raise ParseError(f"surface/distance not found: {race_id}")
    surface = "ダート" if surface_m.group(1) in ("ダ", "ダート") else surface_m.group(1)

    grade = _grade(name) or _grade(meta_text)

    date_el = soup.select_one(".race_otherdata p") or soup.select_one(".smalltxt")
    race_date = parse_jp_date(clean(date_el.get_text())) if date_el else None
    if race_date is None:
        # 偽日付で埋めると時系列分析が静かに壊れるので fail-fast (LINE 通知で検知)。
        raise ParseError(f"race_date not found: {race_id}")

    course_m = re.search(r"\d回(\S+?)\d日", clean(date_el.get_text()) if date_el else "")
    course = course_m.group(1) if course_m else _course_from_race_id(race_id)

    weather_m = _WEATHER_RE.search(meta_text)
    cond_m = _COND_RE.search(meta_text)
    turn_m = _TURN_RE.search(meta_text)

    n_runners = len(soup.select("table.race_table_01 tr")) - 1
    return Race(
        race_id=race_id,
        race_date=race_date,
        course=course,
        race_no=_race_no_from_id(race_id),
        name=name,
        grade=grade,
        surface=surface,
        distance_m=int(distance_m.group(1)),
        turn=turn_m.group(1) if turn_m else None,
        weather=weather_m.group(1) if weather_m else None,
        track_condition=cond_m.group(1) if cond_m else None,
        n_runners=n_runners if n_runners > 0 else None,
        race_class=grade,
        pace_lap=_parse_lap(soup),
    )


def _parse_lap(soup: BeautifulSoup) -> list[float]:
    """ラップ表 (.race_lap_cell 等) があれば 200m 毎ラップを拾う。無ければ空。"""
    cell = soup.select_one("table.race_lap_cell")
    if cell is None:
        return []
    laps = [to_float(td.get_text()) for td in cell.select("td")]
    return [x for x in laps if x is not None]


# race_id = YYYY PP KK DD RR (年/競馬場/開催回/日/レース番号) の netkeiba 慣習に基づく補完。
_COURSE_BY_CODE = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟", "05": "東京",
    "06": "中山", "07": "中京", "08": "京都", "09": "阪神", "10": "小倉",
}


def _course_from_race_id(race_id: str) -> str:
    return _COURSE_BY_CODE.get(race_id[4:6], "不明")


def _race_no_from_id(race_id: str) -> int:
    return to_int(race_id[-2:]) or 0
