"""personal-llm Worker (llm.iwachan.dev) 経由で chat する client。

POST /<URL_SECRET>/chat、X-Auth-Token header。レスポンスは {ok, response, ...}。
briefing 生成専用なので gemini-2.5-flash 固定 (config.LLM_*)、必要なら provider 引数で上書き。
"""

from __future__ import annotations

import httpx

from .. import config


class LLMClient:
    def __init__(self) -> None:
        env = config.require("LLM_BASE_URL", "LLM_URL_SECRET", "LLM_AUTH_TOKEN")
        self._url = f"{env['LLM_BASE_URL'].rstrip('/')}/{env['LLM_URL_SECRET']}/chat"
        self._token = env["LLM_AUTH_TOKEN"]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        provider: str = config.LLM_PROVIDER,
        model: str = config.LLM_MODEL,
        max_tokens: int = config.LLM_MAX_TOKENS,
    ) -> str:
        resp = httpx.post(
            self._url,
            headers={"X-Auth-Token": self._token, "Content-Type": "application/json"},
            json={
                "provider": provider,
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            },
            timeout=httpx.Timeout(120.0),
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"llm error: {data.get('error')}")
        return data["response"]
