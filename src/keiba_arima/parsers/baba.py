"""JRA 馬場情報ページ (クッション値 / 含水率) の parser。

JRA の DOM クラスは公開資料が乏しく変わりやすいので、CSS クラスに依存せず
「行テキストに競馬場名が含まれていれば、その行から数値を拾う」汎用方式にする。
- クッション値ページ: 行 = "中山 9.5" → cushion=9.5
- 含水率ページ: 行 = "中山 芝 12.3% ダート 8.1%" → turf=12.3, dirt=8.1
実 DOM では要検証 (構造変更時は値が欠けるだけで例外は出さない = best-effort)。
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _rows_with_course(html: str) -> dict[str, str]:
    """競馬場名を含む行のテキストを course → row_text で返す。"""
    soup = BeautifulSoup(html, "lxml")
    out: dict[str, str] = {}
    for tr in soup.select("tr"):
        text = tr.get_text(" ", strip=True)
        for course in config.JRA_COURSES:
            if course in text and course not in out:
                out[course] = text
    return out


def parse_cushion(html: str) -> dict[str, float]:
    """course → クッション値。行から最初の小数を採用。"""
    out: dict[str, float] = {}
    for course, text in _rows_with_course(html).items():
        after = text.split(course, 1)[1]
        m = _NUM.search(after)
        if m:
            out[course] = float(m.group())
    return out


def parse_moisture(html: str) -> dict[str, tuple[float | None, float | None]]:
    """course → (芝含水率, ダート含水率)。'芝' / 'ダート' ラベル直後の数値を引き当てる。"""
    out: dict[str, tuple[float | None, float | None]] = {}
    for course, text in _rows_with_course(html).items():
        after = text.split(course, 1)[1]
        turf = _label_value(after, "芝")
        dirt = _label_value(after, "ダート") or _label_value(after, "ダ")
        out[course] = (turf, dirt)
    return out


def _label_value(text: str, label: str) -> float | None:
    idx = text.find(label)
    if idx < 0:
        return None
    m = _NUM.search(text[idx + len(label) :])
    return float(m.group()) if m else None
