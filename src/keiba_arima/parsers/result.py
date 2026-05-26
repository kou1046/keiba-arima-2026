"""race-page の結果テーブル (table.race_table_01) を Result 行に parse。

列順は netkeiba 慣習 (着順/枠/馬番/馬名/性齢/斤量/騎手/タイム/着差/.../通過/上り/単勝/人気/馬体重)。
ヘッダ文字でカラムを引き当てるので多少の列追加には耐える。
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import Result
from . import ParseError
from ._util import clean, horse_id_from_href, time_to_seconds, to_float, to_int

_HEADER_MAP = {
    "着順": "finish",
    "馬名": "horse",
    "騎手": "jockey",
    "斤量": "weight",
    "タイム": "time",
    "着差": "margin",
    "通過": "corner",
    "上り": "up3f",
    "上がり": "up3f",
    "単勝": "odds",
    "人気": "pop",
    "馬体重": "bodyweight",
}


def parse(html: str, race_id: str) -> list[Result]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.race_table_01")
    if table is None:
        raise ParseError(f"result table not found: {race_id}")

    rows = table.select("tr")
    headers = [clean(th.get_text()) for th in rows[0].select("th, td")]
    col = {_HEADER_MAP[h]: i for i, h in enumerate(headers) if h in _HEADER_MAP}
    for need in ("finish", "horse"):
        if need not in col:
            raise ParseError(f"missing column '{need}' in result header: {headers}")

    results: list[Result] = []
    for tr in rows[1:]:
        tds = tr.select("td")
        if len(tds) < len(headers):
            continue
        results.append(_row(tds, col, race_id))
    if not results:
        raise ParseError(f"no result rows: {race_id}")
    return results


def _row(tds, col, race_id: str) -> Result:
    def cell(key: str):
        i = col.get(key)
        return tds[i] if i is not None and i < len(tds) else None

    horse_cell = cell("horse")
    link = horse_cell.find("a") if horse_cell else None
    horse_id = horse_id_from_href(link.get("href") if link else None) or ""

    bw_cell = cell("bodyweight")
    body_kg, body_diff = _body_weight(clean(bw_cell.get_text()) if bw_cell else "")

    return Result(
        race_id=race_id,
        finish_pos=_finish(clean((cell("finish") or _empty()).get_text())),
        horse_id=horse_id,
        horse_name=clean(link.get_text()) if link else clean(horse_cell.get_text() if horse_cell else ""),
        jockey=_text(cell("jockey")),
        weight_carry_kg=to_float(_text(cell("weight"))),
        body_weight_kg=body_kg,
        body_weight_diff=body_diff,
        time_s=time_to_seconds(_text(cell("time"))),
        margin=_text(cell("margin")),
        corner_pos=_corners(_text(cell("corner"))),
        up_3f_s=to_float(_text(cell("up3f"))),
        popularity=to_int(_text(cell("pop"))),
        odds_win=to_float(_text(cell("odds"))),
    )


class _empty:
    def get_text(self) -> str:  # noqa: D401
        return ""


def _text(el) -> str | None:
    return clean(el.get_text()) if el is not None else None


def _finish(s: str) -> int:
    # 中止 / 除外 / 取消 / 失格 等は着外扱い -1。
    n = to_int(s)
    return n if n is not None else -1


def _corners(s: str | None) -> list[int]:
    if not s:
        return []
    return [int(x) for x in re.findall(r"\d+", s)]


def _body_weight(s: str) -> tuple[int | None, int | None]:
    """'498(+4)' → (498, 4)。計不能/--は (None, None)。"""
    m = re.match(r"\s*(\d+)\s*\(([-+]?\d+)\)", s)
    if not m:
        return to_int(s), None
    return int(m.group(1)), int(m.group(2))
