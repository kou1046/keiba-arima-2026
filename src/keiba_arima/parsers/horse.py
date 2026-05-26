"""horse-page (db.netkeiba.com/horse/<horse_id>/) のプロフィールを Horse に parse。

血統表 (.blood_table) から sire / dam / dam_sire、プロフィール表 (.db_prof_table) から
生年月日・調教師・馬主・性別を拾う。性別は出走表側にしか無い場合があり、欠損許容。
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from ..models import Horse
from . import ParseError
from ._util import clean, parse_jp_date

_PROF_LABELS = {
    "生年月日": "birth",
    "調教師": "trainer",
    "馬主": "owner",
}


def parse(html: str, horse_id: str) -> Horse:
    soup = BeautifulSoup(html, "lxml")

    name_el = soup.select_one(".horse_title h1") or soup.select_one("h1")
    if name_el is None:
        raise ParseError(f"horse name not found: {horse_id}")
    name = clean(name_el.get_text())

    prof = _prof_table(soup)
    sire, dam, dam_sire = _blood(soup)

    return Horse(
        horse_id=horse_id,
        name=name,
        sex=_sex(soup),
        birth_date=parse_jp_date(prof.get("birth")),
        sire=sire,
        dam=dam,
        dam_sire=dam_sire,
        trainer=prof.get("trainer"),
        owner=prof.get("owner"),
    )


def _prof_table(soup: BeautifulSoup) -> dict[str, str]:
    out: dict[str, str] = {}
    for tr in soup.select("table.db_prof_table tr"):
        th = tr.find("th")
        td = tr.find("td")
        if th is None or td is None:
            continue
        key = _PROF_LABELS.get(clean(th.get_text()))
        if key:
            out[key] = clean(td.get_text())
    return out


def _blood(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    """blood_table は 父 / 母 / 母父 を含む。行構造から代表 3 つを取る。"""
    table = soup.select_one("table.blood_table")
    if table is None:
        return None, None, None
    names = [clean(a.get_text()) for a in table.select("a")]
    sire = names[0] if names else None
    dam = next((n for n in names if n and n != sire), None)
    # 母父は母ブロックの父。DOM 依存が強いので best-effort で 4 番目あたり。
    dam_sire = names[3] if len(names) > 3 else None
    return sire, dam, dam_sire


def _sex(soup: BeautifulSoup) -> str | None:
    txt = clean((soup.select_one(".horse_title .txt_01") or soup).get_text())
    for s in ("牡", "牝", "セ"):
        if s in txt:
            return s
    return None
