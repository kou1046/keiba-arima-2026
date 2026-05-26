"""Parquet 群の上に DuckDB read-only view を張る。briefing / viz はここから query する。

partition glob (`data/year=*/month=*/<dataset>.parquet`) を read_parquet で束ねるだけ。
year / month はパスから hive partitioning で列として復元される。
"""

from __future__ import annotations

import glob as _glob

import duckdb

from .store import data_dir


def connect() -> duckdb.DuckDBPyConnection:
    """Parquet 群の上に read-only view を張る。まだ 1 件も無い dataset は view を作らない
    (read_parquet が no-match で IOError になるため)。view 不在 = まだ scrape 前。"""
    con = duckdb.connect(":memory:")
    root = data_dir().as_posix()
    for dataset in ("races", "results", "payouts"):
        pattern = f"{root}/year=*/month=*/{dataset}.parquet"
        if _glob.glob(pattern):
            con.execute(
                f"CREATE VIEW {dataset} AS SELECT * FROM "
                f"read_parquet('{pattern}', hive_partitioning = true, union_by_name = true)"
            )
    horses = f"{root}/horses.parquet"
    if _glob.glob(horses):
        con.execute(f"CREATE VIEW horses AS SELECT * FROM read_parquet('{horses}')")
    return con
