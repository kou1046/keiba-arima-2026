"""parser 共通の小物。数値・時刻・日付の頑健なパース。registry には出さない internal。"""

from __future__ import annotations

import re
from datetime import date


def clean(s: str | None) -> str:
    return (s or "").replace("\xa0", " ").strip()


# 重賞グレード。netkeiba は detail ページでローマ数字 (GI/GII/GIII、環境により全角 GⅠ…)、
# list ページではアラビア数字 (G1) と表記揺れがある。長いものから試して G1/G2/G3 に正規化。
_GRADE_RE = re.compile(r"G\s*(Ⅲ|Ⅱ|Ⅰ|III|II|I|[123])")
_GRADE_NORM = {"Ⅰ": "1", "Ⅱ": "2", "Ⅲ": "3", "I": "1", "II": "2", "III": "3", "1": "1", "2": "2", "3": "3"}


def find_grade(text: str | None) -> str | None:
    m = _GRADE_RE.search(text or "")
    return f"G{_GRADE_NORM[m.group(1)]}" if m else None


def to_int(s: str | None) -> int | None:
    s = clean(s)
    m = re.search(r"-?\d+", s.replace(",", ""))
    return int(m.group()) if m else None


def to_float(s: str | None) -> float | None:
    s = clean(s)
    m = re.search(r"-?\d+(?:\.\d+)?", s.replace(",", ""))
    return float(m.group()) if m else None


def time_to_seconds(s: str | None) -> float | None:
    """'1:23.4' / '2:01.8' → 秒。'2.1' のような秒表記も許容。"""
    s = clean(s)
    if not s:
        return None
    if ":" in s:
        m, sec = s.split(":", 1)
        try:
            return int(m) * 60 + float(sec)
        except ValueError:
            return None
    return to_float(s)


def horse_id_from_href(href: str | None) -> str | None:
    """/horse/2019105219/ → 2019105219、海外馬は /horse/000a011996/ → 000a011996。
    JRA は 10 桁数字、海外馬は 16 進 10 桁 (000a で始まる)。サブパス (/horse/ped/, /horse/top.html 等) は除外。"""
    m = re.search(r"/horse/([0-9a-f]{10})(?:/|$|[?#])", href or "")
    return m.group(1) if m else None


def parse_jp_date(s: str | None) -> date | None:
    """'2026年12月28日' / '2026/12/28' → date。"""
    s = clean(s)
    m = re.search(r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})", s)
    if not m:
        return None
    y, mo, d = (int(g) for g in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None
