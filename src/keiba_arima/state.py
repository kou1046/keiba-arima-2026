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
_PARSE_ERRORS_FILE = "parse_errors.json"
_LISTED_DATES_FILE = "listed_dates.json"
_STAKES_CANDIDATES_FILE = "stakes_candidates.json"


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


def listed_dates() -> set[str]:
    """重賞 discovery で list 取得済の日付 (YYYYMMDD)。resume 時の再 list を避ける。"""
    return _load(_LISTED_DATES_FILE)


def mark_listed_dates(days) -> None:
    _save(_LISTED_DATES_FILE, listed_dates() | set(days))


def stakes_candidates() -> set[str]:
    return _load(_STAKES_CANDIDATES_FILE)


def add_stakes_candidates(ids) -> None:
    _save(_STAKES_CANDIDATES_FILE, stakes_candidates() | set(ids))


def append_parse_errors(entries: list[tuple[str, str]]) -> None:
    """parse 失敗を (id, error) で追記。1 レース失敗で job を止めず、後で気付くため。"""
    p = _path(_PARSE_ERRORS_FILE)
    existing = json.loads(p.read_text()) if p.exists() else []
    existing += [{"id": i, "error": e} for i, e in entries]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(existing, ensure_ascii=False, indent=0))
