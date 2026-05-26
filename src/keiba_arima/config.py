"""全 env var / 定数 / scope / rate-limit ポリシーを 1 箇所に集約する。

新しい env や job、scope を足すときはまずここを見る。worker の config.js と同じ思想で、
「何が必要か」を一覧できる状態を保つ (worker-lambda-structure)。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# --- 利用する全 env var ---------------------------------------------------
# source: "secret" = GH Actions secrets / ローカル env。required は使う job で個別に検証する。
ENV_VARS = {
    "LLM_BASE_URL": {
        "source": "vars",
        "purpose": "personal-llm Worker の origin (例: https://llm.iwachan.dev)",
    },
    "LLM_URL_SECRET": {
        "source": "secret",
        "purpose": "personal-llm の path prefix (/<secret>/chat)",
    },
    "LLM_AUTH_TOKEN": {
        "source": "secret",
        "purpose": "personal-llm の X-Auth-Token",
    },
    "R2_ACCOUNT_ID": {
        "source": "secret",
        "purpose": "R2 S3 互換 endpoint の account id",
    },
    "R2_ACCESS_KEY_ID": {
        "source": "secret",
        "purpose": "R2 API token (S3 access key)",
    },
    "R2_SECRET_ACCESS_KEY": {
        "source": "secret",
        "purpose": "R2 API token (S3 secret)",
    },
    "R2_BUCKET": {
        "source": "vars",
        "purpose": "公開ストレージの bucket (既定 iwachan-general)",
    },
    "LINE_CHANNEL_ACCESS_TOKEN": {
        "source": "secret",
        "purpose": "失敗通知の LINE Messaging API token",
    },
    "LINE_USER_ID": {
        "source": "secret",
        "purpose": "通知先 user / group id",
    },
}


def require(*names: str) -> dict[str, str]:
    """指定 env が揃っているか fail-fast で確認して dict で返す。"""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError(f"missing env: {', '.join(missing)}")
    return {n: os.environ[n] for n in names}


# --- netkeiba / rate-limit ポリシー ---------------------------------------
# GH runner の cloud IP は弾かれやすいので保守的に。8s 固定 + jitter、並列なし。
NETKEIBA_BASE = "https://db.netkeiba.com"
REQUEST_INTERVAL_S = 8.0
REQUEST_JITTER_S = 2.0
USER_AGENT = "keiba-arima-2026-scraper/0.1 (+https://github.com/kou1046/keiba-arima-2026)"
MAX_RETRIES = 5  # 403/429/5xx の backoff 上限。超えたら job abort。

# --- R2 公開レイアウト -----------------------------------------------------
R2_PREFIX = "keiba"
R2_BRIEFINGS_PREFIX = f"{R2_PREFIX}/briefings"
R2_INDEX_KEY = f"{R2_PREFIX}/index.json"
PUBLIC_BASE_URL = "https://keiba.iwachan.dev"

# --- 気象庁 forecast (event 1623 第1弾) ----------------------------------
# 認証なしの公開 JSON。中山競馬場は千葉県船橋市 = 「千葉県北西部」エリア。
# 過去レースの天気/馬場は netkeiba 側で取得済なので、これは brief-upcoming で
# 「これから走るレース当日の予報」を briefing に添える用途。
JMA_FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/120000.json"
JMA_AREA_CODE = "120010"  # 千葉県北西部

# --- JRA 馬場情報 (event 1623 第2弾) --------------------------------------
# クッション値 / 含水率。開催前日・当日のみ live、archive あり。当日 cron で fetch して蓄積。
JRA_CUSHION_URL = "https://www.jra.go.jp/keiba/baba/cushion/"
JRA_MOISTURE_URL = "https://www.jra.go.jp/keiba/baba/moist/"
# JRA 中央 10 競馬場 (baba ページの行を引き当てる)。
JRA_COURSES = ("札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉")


# --- LLM ------------------------------------------------------------------
LLM_PROVIDER = "gemini"
LLM_MODEL = "gemini-2.5-flash"
LLM_MAX_TOKENS = 4096


# --- backfill scope -------------------------------------------------------
@dataclass(frozen=True)
class Scope:
    stakes_years: int = 15  # 重賞 (G1/G2/G3) 全競馬場
    nakayama_2500_years: int = 10  # 中山 2500m の平場含む全レース
    horse_history_years: int = 3  # 出走馬の直近戦績


SCOPE = Scope()
