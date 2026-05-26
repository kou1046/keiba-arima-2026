"""scrape 対象 race_id / horse_id の列挙ロジック。

netkeiba の race-list ページ (開催日単位) を起点に列挙する。重賞だけ欲しい場合も
まず list で全 id を得て、fetch 後の grade で絞る (list ページの grade icon 解析は
DOM 依存が強く壊れやすいため、確実な grade 判定は race ページに委ねる)。
"""

from __future__ import annotations

from datetime import date, timedelta


def weekend_dates(years_back: int, today: date | None = None) -> list[date]:
    """過去 years_back 年ぶんの土日を新しい順で返す。中央競馬はほぼ土日開催。"""
    today = today or date.today()
    start = date(today.year - years_back, today.month, today.day)
    out: list[date] = []
    d = today
    while d >= start:
        if d.weekday() in (5, 6):  # Sat, Sun
            out.append(d)
        d -= timedelta(days=1)
    return out


def recent_weekend_dates(days_back: int = 9, today: date | None = None) -> list[date]:
    """直近 days_back 日の土日 (weekly scrape 用、前週末を確実に拾う幅)。"""
    today = today or date.today()
    return [today - timedelta(days=i) for i in range(days_back) if (today - timedelta(days=i)).weekday() in (5, 6)]
