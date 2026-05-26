"""Parquet 蓄積層。races/results/payouts は race_date で year=YYYY/month=MM に partition、
horses は date を持たないので keyed upsert で単一 parquet に置く。

真実の出所は Parquet (commit 対象)。DuckDB はあくまで read-only view (db.py)。
append は「既存読み込み → concat → key で unique (last 優先)」の素朴な upsert。
規模 (~10万行) なら全読みでも軽い。
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import polars as pl

from . import SCHEMA_VERSION
from .clients.netkeiba import RacePage
from .models import Horse

_DATASET_KEYS = {
    "races": ["race_id"],
    "results": ["race_id", "horse_id"],
    "payouts": ["race_id", "ticket_type", "combination"],
}


def data_dir() -> Path:
    return Path(os.environ.get("KEIBA_DATA_DIR", "data"))


def _partition_path(year: int, month: int, dataset: str) -> Path:
    return data_dir() / f"year={year:04d}" / f"month={month:02d}" / f"{dataset}.parquet"


def _rows_to_df(rows: list) -> pl.DataFrame:
    records = [dataclasses.asdict(r) for r in rows]
    df = pl.DataFrame(records)
    return df.with_columns(pl.lit(SCHEMA_VERSION).alias("schema_version"))


def _upsert(path: Path, df: pl.DataFrame, keys: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = pl.read_parquet(path)
        df = pl.concat([existing, df], how="diagonal_relaxed")
    df = df.unique(subset=keys, keep="last", maintain_order=True)
    df.write_parquet(path)


def upsert_race_page(page: RacePage) -> None:
    """1 レース分 (race + results + payouts) を該当 month partition に書き込む。"""
    d = page.race.race_date
    _upsert(_partition_path(d.year, d.month, "races"), _rows_to_df([page.race]), _DATASET_KEYS["races"])
    if page.results:
        _upsert(
            _partition_path(d.year, d.month, "results"),
            _rows_to_df(page.results),
            _DATASET_KEYS["results"],
        )
    if page.payouts:
        _upsert(
            _partition_path(d.year, d.month, "payouts"),
            _rows_to_df(page.payouts),
            _DATASET_KEYS["payouts"],
        )


def upsert_horses(horses: list[Horse]) -> None:
    if not horses:
        return
    path = data_dir() / "horses.parquet"
    _upsert(path, _rows_to_df(horses), ["horse_id"])
