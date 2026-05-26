from pathlib import Path

from keiba_arima.parsers import payout as payout_parser
from keiba_arima.parsers import race as race_parser
from keiba_arima.parsers import result as result_parser

RACE_ID = "202606060811"
HTML = (Path(__file__).parent / "fixtures" / "race_page.html").read_text(encoding="utf-8")


def test_parse_race_meta():
    race = race_parser.parse(HTML, RACE_ID)
    assert race.name.startswith("有馬記念")
    assert race.grade == "G1"
    assert race.surface == "芝"
    assert race.distance_m == 2500
    assert race.turn == "右"
    assert race.weather == "晴"
    assert race.track_condition == "良"
    assert race.course == "中山"
    assert race.n_runners == 2
    assert race.race_date.year == 2026


def test_parse_results():
    results = result_parser.parse(HTML, RACE_ID)
    assert len(results) == 2
    first = results[0]
    assert first.finish_pos == 1
    assert first.horse_id == "2019105219"
    assert first.horse_name == "テスト馬A"
    assert first.weight_carry_kg == 57.0
    assert abs(first.time_s - 150.5) < 0.01  # 2:30.5
    assert first.corner_pos == [3, 3, 2, 2]
    assert first.up_3f_s == 35.1
    assert first.popularity == 2
    assert first.odds_win == 4.5
    assert first.body_weight_kg == 498
    assert first.body_weight_diff == 4
    assert results[1].body_weight_diff == -2


def test_parse_payouts():
    payouts = payout_parser.parse(HTML, RACE_ID)
    by_type = {(p.ticket_type, p.combination): p for p in payouts}
    assert by_type[("単勝", "8")].payout_yen == 450
    assert by_type[("馬連", "4 - 8")].payout_yen == 1280
    # 複勝は <br> 区切りで 2 行に展開される
    assert by_type[("複勝", "8")].payout_yen == 180
    assert by_type[("複勝", "4")].payout_yen == 240
