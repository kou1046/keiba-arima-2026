from pathlib import Path

from keiba_arima.clients.netkeiba import _extract_graded_jra_race_ids
from keiba_arima.parsers._util import find_grade

HTML = (Path(__file__).parent / "fixtures" / "race_list.html").read_text("utf-8")


def test_find_grade_arabic_and_roman():
    assert find_grade("有馬記念(G1)") == "G1"
    assert find_grade("第67回有馬記念(GI)") == "G1"
    assert find_grade("ホープフルS(GIII)") == "G3"
    assert find_grade("阪神カップ(GⅡ)") == "G2"  # 全角ローマ数字
    assert find_grade("りんくうS(OP)") is None
    assert find_grade("3歳以上1勝クラス") is None


def test_extract_graded_jra_race_ids():
    ids = _extract_graded_jra_race_ids(HTML)
    # JRA 重賞だけ: 有馬記念(G1, 中山06) / 阪神カップ(G2, 阪神09) / ホープフルS(G3, 東京05)
    assert set(ids) == {"202206050811", "202209060810", "202205050812"}


def test_extract_excludes_nar_and_non_graded():
    ids = set(_extract_graded_jra_race_ids(HTML))
    assert "202209060811" not in ids  # りんくうS (OP)
    assert "202206050810" not in ids  # フェアウェルS (平場)
    assert "202236122501" not in ids  # 地方 (コード36)
    assert "202246122505" not in ids  # 東京大賞典 (GI だが地方コード46)
