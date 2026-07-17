"""horse pedigree page (db.netkeiba.com/horse/ped/<horse_id>/) から 3 世代 (父 / 母 / 母父) の
名前と netkeiba 馬 ID を抽出。詳細ページ (/horse/<id>/) には blood_table が無くなったため
専用ページを別途 fetch する。
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

from . import ParseError
from ._util import clean, horse_id_from_href


@dataclass
class Pedigree:
    sire_name: str | None
    sire_id: str | None
    dam_name: str | None
    dam_id: str | None
    dam_sire_name: str | None
    dam_sire_id: str | None


def parse(html: str, horse_id: str) -> Pedigree:
    soup = BeautifulSoup(html, "lxml")
    bt = soup.select_one("table.blood_table")
    if bt is None:
        raise ParseError(f"blood_table not found on ped page: {horse_id}")

    # rowspan=16 のセルが 2 つ: 父 (class b_ml) と母 (class b_fml)。
    rs16 = [td for td in bt.select("td") if td.get("rowspan") == "16"]
    sire_td = next((td for td in rs16 if "b_ml" in (td.get("class") or [])), None)
    dam_td = next((td for td in rs16 if "b_fml" in (td.get("class") or [])), None)
    if sire_td is None or dam_td is None:
        raise ParseError(f"sire/dam cell not found: {horse_id}")

    sire_name, sire_id = _name_and_id(sire_td)
    dam_name, dam_id = _name_and_id(dam_td)

    # 母父 = 母行内の rowspan=8 b_ml セル。母の <td> と同じ <tr> 内に並ぶ。
    dam_tr = dam_td.find_parent("tr")
    dam_sire_td = None
    if dam_tr is not None:
        for td in dam_tr.select("td"):
            if td is dam_td:
                continue
            if td.get("rowspan") == "8" and "b_ml" in (td.get("class") or []):
                dam_sire_td = td
                break
    dam_sire_name, dam_sire_id = _name_and_id(dam_sire_td) if dam_sire_td else (None, None)

    return Pedigree(
        sire_name=sire_name,
        sire_id=sire_id,
        dam_name=dam_name,
        dam_id=dam_id,
        dam_sire_name=dam_sire_name,
        dam_sire_id=dam_sire_id,
    )


def _name_and_id(td) -> tuple[str | None, str | None]:
    a = td.select_one("a")
    if a is None:
        return _normalize_name(td.get_text()), None
    return _normalize_name(a.get_text()), horse_id_from_href(a.get("href"))


def _normalize_name(s: str | None) -> str | None:
    """blood_table の anchor は \"ハービンジャー\\n\\tHarbinger(英)\" のように改行/タブで JP / Latin が
    連結されることがある。連続空白を 1 つに畳んで返す。"""
    s = clean(s)
    if not s:
        return None
    return " ".join(s.split())
