from datetime import date

from keiba_arima import db, store, viz
from keiba_arima.clients.netkeiba import RacePage
from keiba_arima.models import Payout, Race, Result

RACE_ID = "202606060811"


def _page() -> RacePage:
    race = Race(
        race_id=RACE_ID,
        race_date=date(2026, 12, 28),
        course="中山",
        race_no=11,
        name="有馬記念",
        grade="G1",
        surface="芝",
        distance_m=2500,
        turn="右",
        weather="晴",
        track_condition="良",
        n_runners=2,
        race_class="G1",
        pace_lap=[],
    )
    results = [
        Result(RACE_ID, 1, "2019105219", "テスト馬A", "テス騎手", 57.0, 498, 4, 150.5,
               None, [3, 3, 2, 2], 35.1, 2, 4.5),
        Result(RACE_ID, 2, "2018102345", "テスト馬B", "別騎手", 55.0, 470, -2, 150.6,
               "クビ", [5, 5, 5, 4], 34.9, 3, 6.2),
    ]
    payouts = [Payout(RACE_ID, "単勝", "8", 450, 2)]
    return RacePage(race, results, payouts)


def test_store_roundtrip_and_views(tmp_path, monkeypatch):
    monkeypatch.setenv("KEIBA_DATA_DIR", str(tmp_path))
    store.upsert_race_page(_page())
    # 同じ page を再投入しても unique で増えない
    store.upsert_race_page(_page())

    assert (tmp_path / "year=2026" / "month=12" / "races.parquet").exists()

    con = db.connect()
    try:
        assert con.execute("SELECT COUNT(*) FROM races").fetchone()[0] == 1
        assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 2
        name = con.execute("SELECT name FROM races WHERE race_id = ?", [RACE_ID]).fetchone()[0]
        assert name == "有馬記念"

        charts = viz.render_all(con, RACE_ID)
        assert "corner_positioning" in charts
        assert "popularity_vs_finish" in charts
        assert charts["corner_positioning"].startswith(b"<?xml")
    finally:
        con.close()
