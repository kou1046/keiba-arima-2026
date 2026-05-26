"""気象庁 forecast JSON の取得 (event 1623 第1弾)。認証なし・通常 polling で OK。

netkeiba と違い rate 配慮不要なので http.py は使わず httpx 直。parse は network に
触れない純粋関数 (parse_forecast) に分け、fixture でテストできるようにする。
中山 = 千葉県北西部 (config.JMA_AREA_CODE) の天気 / 降水確率 / 気温を要約する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from .. import config


@dataclass
class ForecastSummary:
    area_name: str
    weathers: list[tuple[str, str]] = field(default_factory=list)  # (日時, 天気)
    pops: list[tuple[str, str]] = field(default_factory=list)  # (日時, 降水確率%)
    temps: list[tuple[str, str]] = field(default_factory=list)  # (日時, 気温℃)

    def as_note(self) -> str:
        """briefing context に差し込む人間可読の短い文字列。"""
        lines = [f"気象 (気象庁予報 / {self.area_name}):"]
        for when, w in self.weathers[:3]:
            lines.append(f"- {when}: {w}")
        if self.pops:
            lines.append("降水確率: " + ", ".join(f"{t}={p}%" for t, p in self.pops[:4]))
        if self.temps:
            lines.append("気温: " + ", ".join(f"{t}={v}℃" for t, v in self.temps[:4]))
        return "\n".join(lines)


def _area(areas: list, area_code: str) -> dict | None:
    for a in areas:
        if a.get("area", {}).get("code") == area_code:
            return a
    return areas[0] if areas else None


def parse_forecast(payload: list, area_code: str) -> ForecastSummary:
    """forecast JSON ([0] が短期予報) から指定エリアの天気/降水/気温を抜く。"""
    near = payload[0]
    series = near.get("timeSeries", [])
    summary = ForecastSummary(area_name="")

    if series:
        wt = series[0]
        times = wt.get("timeDefines", [])
        area = _area(wt.get("areas", []), area_code) or {}
        summary.area_name = area.get("area", {}).get("name", area_code)
        summary.weathers = list(zip(times, area.get("weathers", [])))
    if len(series) > 1:
        pt = series[1]
        times = pt.get("timeDefines", [])
        area = _area(pt.get("areas", []), area_code) or {}
        summary.pops = list(zip(times, area.get("pops", [])))
    if len(series) > 2:
        tt = series[2]
        times = tt.get("timeDefines", [])
        area = _area(tt.get("areas", []), area_code) or {}
        summary.temps = list(zip(times, area.get("temps", [])))
    return summary


class JMAClient:
    def __init__(self) -> None:
        self._url = config.JMA_FORECAST_URL
        self._area = config.JMA_AREA_CODE

    def latest_forecast(self) -> ForecastSummary:
        resp = httpx.get(self._url, timeout=httpx.Timeout(15.0))
        resp.raise_for_status()
        return parse_forecast(resp.json(), self._area)
