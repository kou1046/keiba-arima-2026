from pathlib import Path

from keiba_arima.clients.netkeiba import _extract_horse_race_ids

HTML = (Path(__file__).parent / "fixtures" / "horse_page.html").read_text("utf-8")


def test_extract_only_results_table_links():
    ids = _extract_horse_race_ids(HTML)
    # 戦績テーブル内の 3 件のみ。テーブル外のナビリンクは除外。
    assert ids == ["202206050811", "202205050812", "202106050811"]
    assert "209900000000" not in ids


def test_year_filter_logic():
    ids = _extract_horse_race_ids(HTML)
    in_2022 = [r for r in ids if r[:4] == "2022"]
    assert in_2022 == ["202206050811", "202205050812"]
    since_2022 = [r for r in ids if int(r[:4]) >= 2022]
    assert since_2022 == ["202206050811", "202205050812"]
