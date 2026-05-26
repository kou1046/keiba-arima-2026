"""DuckDB の生データから context を組み立て、personal-llm で briefing / review markdown を生成。

LLM には「DB から抜いた構造化テキスト」だけを渡し、固有名の捏造を防ぐ (prompt 側でも禁止)。
生成 markdown の冒頭に viz チャートを埋め込む (chart_urls)。
"""

from __future__ import annotations

from importlib import resources

from .clients.llm import LLMClient

_MAX_RESULT_ROWS = 18


def _prompt(name: str) -> str:
    return resources.files("keiba_arima.prompts").joinpath(name).read_text(encoding="utf-8")


def build_context(con, race_id: str, weather_note: str = "", pre_race: bool = False) -> str:
    """race メタ + 結果/出走表を LLM 用の plain text に整形。
    weather_note は brief-upcoming 時に気象庁/JRA 馬場情報を添える用 (空なら省略)。
    pre_race=True (レース前) は finish_pos が無いので人気順、False は着順で並べる。"""
    race = con.execute(
        "SELECT name, race_date, course, surface, distance_m, turn, weather, "
        "track_condition, grade, n_runners FROM races WHERE race_id = ?",
        [race_id],
    ).fetchone()
    if race is None:
        raise ValueError(f"race not found in db: {race_id}")
    name, rdate, course, surface, dist, turn, weather, cond, grade, n = race

    lines = [
        f"race_id: {race_id}",
        f"レース名: {name} ({grade or '-'})",
        f"日付: {rdate}  競馬場: {course}  {surface}{dist}m {turn or ''}",
        f"天候: {weather or '-'}  馬場: {cond or '-'}  頭数: {n or '-'}",
        "",
        "## 結果 / 出走 (着順, 馬名, 騎手, 斤量, タイム, 上り3F, 人気, 単勝)",
    ]
    order_by = (
        "popularity ASC NULLS LAST"
        if pre_race
        else "CASE WHEN finish_pos > 0 THEN finish_pos ELSE 999 END"
    )
    rows = con.execute(
        "SELECT finish_pos, horse_name, jockey, weight_carry_kg, time_s, up_3f_s, "
        f"popularity, odds_win FROM results WHERE race_id = ? ORDER BY {order_by} LIMIT ?",
        [race_id, _MAX_RESULT_ROWS],
    ).fetchall()
    for fp, hn, jk, wt, t, up, pop, odds in rows:
        lines.append(
            f"- {fp if fp > 0 else '着外'}: {hn} / {jk or '-'} / {wt or '-'}kg / "
            f"{t or '-'}s / 上り{up or '-'} / {pop or '-'}人気 / {odds or '-'}倍"
        )
    if weather_note:
        lines += ["", weather_note]
    return "\n".join(lines)


def generate_briefing(
    con,
    race_id: str,
    chart_urls: dict[str, str],
    weather_note: str = "",
    llm: LLMClient | None = None,
) -> str:
    llm = llm or LLMClient()
    system = _prompt("briefing_system.md")
    few_shot = _prompt("briefing_few_shot.md")
    context = build_context(con, race_id, weather_note, pre_race=True)
    body = llm.chat(
        [
            {"role": "system", "content": f"{system}\n\n{few_shot}"},
            {"role": "user", "content": context},
        ]
    )
    return _embed_charts(body, chart_urls)


def generate_review(
    con, race_id: str, prior_briefing: str, chart_urls: dict[str, str], llm: LLMClient | None = None
) -> str:
    llm = llm or LLMClient()
    system = _prompt("review_system.md")
    context = build_context(con, race_id)
    user = f"# レース結果データ\n{context}\n\n# 事前 briefing\n{prior_briefing or '(なし)'}"
    body = llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
    return _embed_charts(body, chart_urls)


def _embed_charts(markdown: str, chart_urls: dict[str, str]) -> str:
    if not chart_urls:
        return markdown
    imgs = "\n".join(f"![{name}]({url})" for name, url in chart_urls.items())
    return f"{markdown}\n\n## データ可視化\n{imgs}\n"
