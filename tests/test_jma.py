import json
from pathlib import Path

from keiba_arima.clients.jma import parse_forecast

PAYLOAD = json.loads((Path(__file__).parent / "fixtures" / "jma_forecast.json").read_text("utf-8"))


def test_parse_forecast_picks_area():
    s = parse_forecast(PAYLOAD, "120010")
    assert s.area_name == "千葉県北西部"
    assert s.weathers[0] == ("2026-12-27T17:00:00+09:00", "晴れ")
    assert ("2026-12-28T06:00:00+09:00", "10") in s.pops
    # 気温は point station にフォールバック (北西部の temps が無いケース)
    assert s.temps[-1] == ("2026-12-28T09:00:00+09:00", "12")


def test_as_note_is_compact_text():
    note = parse_forecast(PAYLOAD, "120010").as_note()
    assert "千葉県北西部" in note
    assert "晴れ" in note
    assert "降水確率" in note
