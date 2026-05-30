"""血統 (sire / dam / dam_sire と各馬 ID) を /horse/ped/<id>/ から backfill する。

旧 parser は blood_table を /horse/<id>/ から取ろうとしていたが、現行ページには無く、
horses.parquet の sire/dam/dam_sire は全て NULL になっていた。本 job は:
  1. 起動時に horses.parquet の壊れた int 列をドロップ (idempotent migration)
  2. results に出現する horse_id ∪ 既存 horses.parquet を母集合とする
  3. scraped_pedigree.json で未取得分を resume
  4. 各馬 client.fetch_horse() を呼び (詳細 + 血統ページ 2 リクエスト)、horses.parquet に upsert

backfill_horses (詳細 + 戦績) とは独立。新規馬の戦績クロールは backfill_horses が担当する。
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from .. import db, state, store
from ..clients.netkeiba import NetkeibaClient
from . import run

log = logging.getLogger(__name__)

_LEGACY_INT_COLS = ("sire", "dam", "dam_sire")


def _migrate_horses_parquet(path: Path) -> None:
    """旧スキーマ (sire/dam/dam_sire が int32 で全 NULL) のままだと str との concat で型衝突するため、
    起動時に該当列をドロップして書き戻す。新スキーマ書き込み済なら no-op。"""
    if not path.exists():
        return
    df = pl.read_parquet(path)
    to_drop = [c for c in _LEGACY_INT_COLS if c in df.columns and df[c].dtype != pl.Utf8]
    if not to_drop:
        return
    log.info("migrating horses.parquet: dropping legacy int cols %s", to_drop)
    df.drop(to_drop).write_parquet(path)


def _target_horse_ids() -> list[str]:
    """results に登場する馬 ∪ 既存 horses.parquet の馬。重複は除く。"""
    con = db.connect()
    try:
        rows = con.execute(
            "SELECT DISTINCT horse_id FROM results WHERE horse_id <> ''"
        ).fetchall()
    finally:
        con.close()
    from_results = {r[0] for r in rows}

    horses_path = store.data_dir() / "horses.parquet"
    from_horses: set[str] = set()
    if horses_path.exists():
        from_horses = set(pl.read_parquet(horses_path)["horse_id"].to_list())

    return sorted(from_results | from_horses)


def _main() -> None:
    horses_path = store.data_dir() / "horses.parquet"
    _migrate_horses_parquet(horses_path)

    targets = _target_horse_ids()
    pending = state.pending_pedigree(targets)
    log.info("pedigree backfill: %d targets, %d pending", len(targets), len(pending))

    client = NetkeibaClient()
    try:
        for i, horse_id in enumerate(pending, 1):
            horse = client.fetch_horse(horse_id)
            store.upsert_horses([horse])
            state.mark_pedigree([horse_id])
            # 詳細ページ取得済なので scraped_horses にも反映 (backfill_horses の戦績クロールが
            # 別途必要だが、二重 fetch を避けるためここで詳細取得済フラグを立てる)
            state.mark_horses([horse_id])
            if i % 50 == 0:
                log.info("progress: %d / %d", i, len(pending))
    finally:
        client.close()


def main() -> None:
    run("backfill_pedigree", _main)


if __name__ == "__main__":
    main()
