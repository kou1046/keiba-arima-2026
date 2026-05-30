"""horse-page (db.netkeiba.com/horse/<horse_id>/) のプロフィールを Horse に parse。

プロフィール表 (.db_prof_table) から生年月日・調教師・馬主、ヘッダから性別を拾う。
性別は出走表側にしか無い場合があり、欠損許容。
血統 (sire/dam/dam_sire) は別ページ /horse/ped/<id>/ に移ったため parsers/pedigree.py で別途取得し、
client 層でマージする。
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

    return Horse(
        horse_id=horse_id,
        name=name,
        sex=_sex(soup),
        birth_date=parse_jp_date(prof.get("birth")),
        sire=None,
        sire_id=None,
        dam=None,
        dam_id=None,
        dam_sire=None,
        dam_sire_id=None,
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


def _sex(soup: BeautifulSoup) -> str | None:
    txt = clean((soup.select_one(".horse_title .txt_01") or soup).get_text())
    for s in ("牡", "牝", "セ"):
        if s in txt:
            return s
    return None
