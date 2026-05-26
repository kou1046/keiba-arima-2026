"""parser 共通の小物。数値・時刻・日付の頑健なパース。registry には出さない internal。"""

from __future__ import annotations

import re
from datetime import date


def clean(s: str | None) -> str:
    return (s or "").replace("\xa0", " ").strip()


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
    """/horse/2019105219/ → 2019105219。"""
    m = re.search(r"/horse/(\d+)", href or "")
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
