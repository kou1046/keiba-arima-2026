"""netkeiba HTML → models dataclass の parser 群。

各 parser は HTML 文字列を受け取り dataclass を返す純粋関数。network には触れない
(取得は http.py、呼び出しは jobs)。これにより tests/ で fixture HTML を食わせて検証できる。

注意: netkeiba の DOM は予告なく変わる。parser は必須カラム欠損を ParseError で上げ、
job 側の validation step が検知して LINE 通知 → 早期 fail する想定 (設計書「既知のリスク」)。
"""

from __future__ import annotations


class ParseError(Exception):
    """必須要素が見つからない / 想定外の DOM。job を fail させる。"""
