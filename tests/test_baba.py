from datetime import date
from pathlib import Path

from keiba_arima.clients.jra import merge_conditions
from keiba_arima.parsers import baba

FIX = Path(__file__).parent / "fixtures"
CUSHION = (FIX / "jra_cushion.html").read_text("utf-8")
MOISTURE = (FIX / "jra_moisture.html").read_text("utf-8")


def test_parse_cushion():
    c = baba.parse_cushion(CUSHION)
    assert c["中山"] == 9.5
    assert c["阪神"] == 8.8
    assert c["東京"] == 9.1


def test_parse_moisture():
    m = baba.parse_moisture(MOISTURE)
    assert m["中山"] == (12.3, 8.1)
    assert m["阪神"] == (15.0, 9.4)


def test_merge_conditions_orders_by_jra_courses():
    conds = merge_conditions(CUSHION, MOISTURE, date(2026, 12, 28))
    by_course = {c.course: c for c in conds}
    nakayama = by_course["中山"]
    assert nakayama.cushion_value == 9.5
    assert nakayama.turf_moisture == 12.3
    assert nakayama.dirt_moisture == 8.1
    # 東京は cushion のみ (moisture 無し) でも行が出る
    assert by_course["東京"].cushion_value == 9.1
    assert by_course["東京"].turf_moisture is None
