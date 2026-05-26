"""生データの SVG グラフ可視化 (ML は入れない方針 / event 1622)。

最初の 3 種:
  1. finish_trend       … 出走各馬の過去戦績の着順推移 (horses history join)
  2. corner_positioning … そのレースのコーナー通過順位の推移
  3. popularity_vs_finish … 人気 vs 着順 の散布

捏造リスクのない「生データの構造提示」に徹する。Claude Vision も読めるよう SVG。
ラベルは font tofu を避けるため ASCII 主体。出力は {name: svg_bytes}。
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_MAX_HORSES = 8  # 上位人気/上位着順だけ描く。全頭描くと線が潰れる。


def _svg(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def render_all(con, race_id: str) -> dict[str, bytes]:
    """results が揃っているレースについて 3 種を生成。無ければ空 dict。"""
    results = con.execute(
        "SELECT horse_id, horse_name, finish_pos, popularity, corner_pos "
        "FROM results WHERE race_id = ? ORDER BY finish_pos",
        [race_id],
    ).fetchall()
    if not results:
        return {}
    charts: dict[str, bytes] = {}
    charts["corner_positioning"] = _corner_positioning(results)
    charts["popularity_vs_finish"] = _popularity_vs_finish(results)
    trend = _finish_trend(con, race_id)
    if trend is not None:
        charts["finish_trend"] = trend
    return charts


def _corner_positioning(results) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 4))
    for horse_id, name, finish, _pop, corners in results[:_MAX_HORSES]:
        if not corners:
            continue
        ax.plot(range(1, len(corners) + 1), corners, marker="o", label=f"{finish}: {horse_id}")
    ax.invert_yaxis()  # 上位 = 上
    ax.set_xlabel("corner #")
    ax.set_ylabel("position")
    ax.set_title("Corner positioning (top finishers)")
    ax.legend(fontsize=7, loc="best")
    return _svg(fig)


def _popularity_vs_finish(results) -> bytes:
    fig, ax = plt.subplots(figsize=(5, 5))
    xs = [r[3] for r in results if r[3] is not None and r[2] > 0]
    ys = [r[2] for r in results if r[3] is not None and r[2] > 0]
    ax.scatter(xs, ys)
    lim = max(xs + ys + [1])
    ax.plot([0, lim], [0, lim], linestyle="--", linewidth=0.8)  # 人気=着順の対角
    ax.set_xlabel("popularity (odds rank)")
    ax.set_ylabel("finish position")
    ax.set_title("Popularity vs finish")
    return _svg(fig)


def _finish_trend(con, race_id: str) -> bytes | None:
    """このレースの出走馬それぞれの過去レース着順を時系列で。"""
    rows = con.execute(
        """
        SELECT r.horse_id, r.race_id, ra.race_date, r.finish_pos
        FROM results r
        JOIN races ra ON ra.race_id = r.race_id
        WHERE r.horse_id IN (SELECT horse_id FROM results WHERE race_id = ?)
          AND r.finish_pos > 0
        ORDER BY r.horse_id, ra.race_date
        """,
        [race_id],
    ).fetchall()
    if len(rows) < 2:
        return None
    by_horse: dict[str, list[tuple]] = {}
    for horse_id, _rid, rdate, finish in rows:
        by_horse.setdefault(horse_id, []).append((rdate, finish))
    fig, ax = plt.subplots(figsize=(7, 4))
    for horse_id, series in list(by_horse.items())[:_MAX_HORSES]:
        dates = [s[0] for s in series]
        finishes = [s[1] for s in series]
        ax.plot(dates, finishes, marker="o", label=horse_id)
    ax.invert_yaxis()
    ax.set_xlabel("race date")
    ax.set_ylabel("finish position")
    ax.set_title("Finish position trend (entrants' history)")
    ax.legend(fontsize=7, loc="best")
    fig.autofmt_xdate()
    return _svg(fig)
