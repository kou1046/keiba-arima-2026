"""race-page の払戻テーブル (.pay_block / table.pay_table_01) を Payout 行に parse。

券種ごとに combination / payout / popularity が並ぶ。複勝・ワイドは複数行を内包するので
<br> 区切りを行ごとに展開する。
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from ..models import Payout
from ._util import clean, to_int

# th のラベル → ticket_type 正規化
_TICKETS = {"単勝", "複勝", "枠連", "馬連", "ワイド", "馬単", "三連複", "3連複", "三連単", "3連単"}


def parse(html: str, race_id: str) -> list[Payout]:
    soup = BeautifulSoup(html, "lxml")
    payouts: list[Payout] = []
    for table in soup.select("table.pay_table_01"):
        for tr in table.select("tr"):
            th = tr.find("th")
            tds = tr.select("td")
            if th is None or len(tds) < 2:
                continue
            ticket = clean(th.get_text())
            if ticket not in _TICKETS:
                continue
            combos = _split_br(tds[0])
            yens = _split_br(tds[1])
            pops = _split_br(tds[2]) if len(tds) > 2 else []
            for i, combo in enumerate(combos):
                yen = to_int(yens[i]) if i < len(yens) else None
                if yen is None:
                    continue
                payouts.append(
                    Payout(
                        race_id=race_id,
                        ticket_type=ticket,
                        combination=combo,
                        payout_yen=yen,
                        popularity=to_int(pops[i]) if i < len(pops) else None,
                    )
                )
    return payouts


def _split_br(td) -> list[str]:
    """<td>7 - 12<br>3 - 7</td> → ['7 - 12', '3 - 7']。"""
    parts: list[str] = []
    buf: list[str] = []
    for node in td.children:
        if getattr(node, "name", None) == "br":
            parts.append(clean("".join(buf)))
            buf = []
        else:
            buf.append(node.get_text() if hasattr(node, "get_text") else str(node))
    parts.append(clean("".join(buf)))
    return [p for p in parts if p]
