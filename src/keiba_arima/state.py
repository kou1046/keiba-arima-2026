"""取得済 race_id / horse_id を記録して resume を可能にする (data/_state/*.json)。

job が IP block で死んでも push 済の state があれば次回 trigger で続きから。
集合の積集合で「まだ取ってない id」を出すだけの薄いユーティリティ。
"""

from __future__ import annotations

import json
from pathlib import Path

from .store import data_dir

_RACES_FILE = "scraped_races.json"
_HORSES_FILE = "scraped_horses.json"


def _path(name: str) -> Path:
    return data_dir() / "_state" / name


def _load(name: str) -> set[str]:
    p = _path(name)
    if not p.exists():
        return set()
    return set(json.loads(p.read_text()))


def _save(name: str, ids: set[str]) -> None:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=0))


def scraped_races() -> set[str]:
    return _load(_RACES_FILE)


def mark_races(ids) -> None:
    _save(_RACES_FILE, scraped_races() | set(ids))


def pending_races(candidates) -> list[str]:
    done = scraped_races()
    return [c for c in candidates if c not in done]


def scraped_horses() -> set[str]:
    return _load(_HORSES_FILE)


def mark_horses(ids) -> None:
    _save(_HORSES_FILE, scraped_horses() | set(ids))


def pending_horses(candidates) -> list[str]:
    done = scraped_horses()
    return [c for c in candidates if c not in done]
