"""netkeiba からの取得を 1 箇所に集約。http.py (rate-limited) を内部に持ち、
parsers で dataclass に変換して返す。race_id / horse_id の列挙もここ。
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup

from .. import config
from ..http import RateLimitedClient
from ..models import Horse, Payout, Race, Result
from ..parsers import horse as horse_parser
from ..parsers import payout as payout_parser
from ..parsers import race as race_parser
from ..parsers import result as result_parser
from ..parsers._util import find_grade

# JRA 中央 10 競馬場の race_id 競馬場コード (01-10)。これ以外 (30番台/40番台) は地方競馬。
_JRA_COURSE_CODES = {f"{i:02d}" for i in range(1, 11)}


class RacePage:
    """1 race-page 取得で得られる race / results / payouts のまとまり。"""

    def __init__(self, race: Race, results: list[Result], payouts: list[Payout]) -> None:
        self.race = race
        self.results = results
        self.payouts = payouts


class NetkeibaClient:
    def __init__(self, http: RateLimitedClient | None = None) -> None:
        self._http = http or RateLimitedClient()
        self._owns_http = http is None

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def fetch_race(self, race_id: str) -> RacePage:
        html = self._http.get_html(f"{config.NETKEIBA_BASE}/race/{race_id}/")
        return RacePage(
            race=race_parser.parse(html, race_id),
            results=result_parser.parse(html, race_id),
            payouts=payout_parser.parse(html, race_id),
        )

    def fetch_horse(self, horse_id: str) -> Horse:
        html = self._http.get_html(f"{config.NETKEIBA_BASE}/horse/{horse_id}/")
        return horse_parser.parse(html, horse_id)

    def list_race_ids_on(self, day: date) -> list[str]:
        """開催日の全 race_id を race_list ページから列挙する。"""
        url = f"{config.NETKEIBA_BASE}/race/list/{day:%Y%m%d}/"
        html = self._http.get_html(url)
        return _extract_race_ids(html)

    def list_graded_race_ids_on(self, day: date) -> list[str]:
        """開催日の JRA 重賞 (G1/G2/G3) race_id だけを list ページから列挙する。

        list ページは link テキストにグレードを含む (例 '有馬記念(G1)') ので、全レースを
        fetch せずここで重賞だけに絞れる (backfill-stakes の fetch 量を ~50k→~2k に削減)。
        """
        url = f"{config.NETKEIBA_BASE}/race/list/{day:%Y%m%d}/"
        html = self._http.get_html(url)
        return _extract_graded_jra_race_ids(html)

    def list_horse_race_ids(self, horse_id: str, since: date) -> list[str]:
        """馬の戦績ページから since 以降 (年単位) に出走した race_id を列挙する。"""
        html = self._http.get_html(f"{config.NETKEIBA_BASE}/horse/{horse_id}/")
        return [r for r in _extract_horse_race_ids(html) if int(r[:4]) >= since.year]

    def list_horse_race_ids_in_year(self, horse_id: str, year: int) -> list[str]:
        """馬の戦績ページから「指定年」に出走した race_id だけを列挙する。

        過去の対象レース (例: 2015 有馬記念) 出走馬の、その年のキャンペーンを埋める用途。
        """
        html = self._http.get_html(f"{config.NETKEIBA_BASE}/horse/{horse_id}/")
        return [r for r in _extract_horse_race_ids(html) if r[:4] == f"{year:04d}"]


_RACE_HREF_RE = re.compile(r"/race/(\d{12})")


def _extract_race_ids(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    ids = [_race_id_from_href(a.get("href")) for a in soup.select("a[href*='/race/']")]
    return _dedup([i for i in ids if i])


def _extract_horse_race_ids(html: str) -> list[str]:
    """馬個別ページの戦績テーブルから出走 race_id を列挙する (年フィルタは呼び出し側)。"""
    soup = BeautifulSoup(html, "lxml")
    ids = [
        _race_id_from_href(a.get("href"))
        for a in soup.select("table.db_h_race_results a[href*='/race/']")
    ]
    return _dedup([i for i in ids if i])


def _extract_graded_jra_race_ids(html: str) -> list[str]:
    """list ページの各レースリンクから、JRA (コード 01-10) かつグレード表記を持つものだけ。"""
    soup = BeautifulSoup(html, "lxml")
    out: list[str] = []
    for a in soup.select("a[href*='/race/']"):
        rid = _race_id_from_href(a.get("href"))
        if rid is None or rid[4:6] not in _JRA_COURSE_CODES:
            continue
        if find_grade(a.get_text()) is not None:
            out.append(rid)
    return _dedup(out)


def _race_id_from_href(href: str | None) -> str | None:
    m = _RACE_HREF_RE.search(href or "")
    return m.group(1) if m else None


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
