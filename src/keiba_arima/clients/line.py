"""失敗通知用 LINE Messaging API push client。minecraft-aws-server-ops の Pochi 声で統一。

job が落ちたとき jobs 側 (or workflow の on:failure) から notify() を叩く。env が無ければ no-op。
"""

from __future__ import annotations

import os

import httpx

_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def notify(text: str) -> bool:
    """LINE に push。env 未設定なら何もせず False を返す (通知系で本処理を巻き込まない)。"""
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user = os.environ.get("LINE_USER_ID")
    if not token or not user:
        return False
    resp = httpx.post(
        _PUSH_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"to": user, "messages": [{"type": "text", "text": text}]},
        timeout=httpx.Timeout(15.0),
    )
    return resp.status_code == 200
