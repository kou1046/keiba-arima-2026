"""R2 への briefing / chart アップロードと index.json 更新の機構。

R2 key 構造 (config.R2_BRIEFINGS_PREFIX = keiba/briefings):
  keiba/briefings/<race-id>/<ts>.md            … briefing
  keiba/briefings/<race-id>/<ts>--review.md     … review
  keiba/briefings/<race-id>/charts/<ts>-<name>.svg
公開 URL は worker が keiba/briefings/ を剥がして配るので PUBLIC_BASE_URL/<race-id>/... になる。
"""

from __future__ import annotations

import json

from . import config
from .clients.r2 import R2Client


def _briefing_key(race_id: str, ts: str, is_review: bool) -> str:
    suffix = "--review" if is_review else ""
    return f"{config.R2_BRIEFINGS_PREFIX}/{race_id}/{ts}{suffix}.md"


def _chart_key(race_id: str, ts: str, name: str) -> str:
    return f"{config.R2_BRIEFINGS_PREFIX}/{race_id}/charts/{ts}-{name}.svg"


def _public_url(key: str) -> str:
    rel = key[len(config.R2_BRIEFINGS_PREFIX) + 1 :]  # <race-id>/...
    return f"{config.PUBLIC_BASE_URL}/{rel}"


def upload_charts(r2: R2Client, race_id: str, ts: str, charts: dict[str, bytes]) -> dict[str, str]:
    urls: dict[str, str] = {}
    for name, svg in charts.items():
        key = _chart_key(race_id, ts, name)
        r2.put(key, svg, "image/svg+xml")
        urls[name] = _public_url(key)
    return urls


def upload_briefing(
    r2: R2Client, race_id: str, ts: str, markdown: str, is_review: bool
) -> tuple[str, str]:
    """markdown を上げて (r2_key, public_url) を返す。key は index 追記・後の review 取得に使う。"""
    key = _briefing_key(race_id, ts, is_review)
    r2.put_text(key, markdown, "text/markdown; charset=utf-8")
    return key, _public_url(key)


def update_index(r2: R2Client, entry: dict) -> None:
    """全 briefing メタの一覧 index.json に entry を 1 件追記 (重複 url は上書き)。"""
    raw = r2.get_text(config.R2_INDEX_KEY)
    index = json.loads(raw) if raw else {"briefings": []}
    index["briefings"] = [b for b in index["briefings"] if b.get("url") != entry["url"]]
    index["briefings"].append(entry)
    index["briefings"].sort(key=lambda b: b.get("generated_at", ""), reverse=True)
    r2.put_text(config.R2_INDEX_KEY, json.dumps(index, ensure_ascii=False, indent=2), "application/json")
