"""Parquet schema に対応する row dataclass。parser が生成し store が書き出す。

設計書の races / results / horses / payouts に 1:1 対応。schema を変えたら
keiba_arima.SCHEMA_VERSION を上げ、store 側の partition は据え置きで新カラムを追記する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Race:
    race_id: str
    race_date: date
    course: str
    race_no: int
    name: str
    grade: str | None
    surface: str
    distance_m: int
    turn: str | None
    weather: str | None
    track_condition: str | None
    n_runners: int | None
    race_class: str | None
    pace_lap: list[float] = field(default_factory=list)


@dataclass
class Result:
    race_id: str
    finish_pos: int  # 着外 / 取消は -1
    horse_id: str
    horse_name: str
    jockey: str | None
    weight_carry_kg: float | None
    body_weight_kg: int | None
    body_weight_diff: int | None
    time_s: float | None
    margin: str | None
    corner_pos: list[int] = field(default_factory=list)
    up_3f_s: float | None = None
    popularity: int | None = None
    odds_win: float | None = None


@dataclass
class Horse:
    horse_id: str
    name: str
    sex: str | None
    birth_date: date | None
    sire: str | None
    dam: str | None
    dam_sire: str | None
    trainer: str | None
    owner: str | None = None


@dataclass
class Payout:
    race_id: str
    ticket_type: str
    combination: str
    payout_yen: int
    popularity: int | None
