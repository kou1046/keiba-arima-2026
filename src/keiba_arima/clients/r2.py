"""R2 (S3 互換) への公開オブジェクト put / get / list。boto3 を S3 endpoint 向けに使う。

bucket は cross-project 共有の iwachan-general、keiba/ prefix 配下 (config.R2_PREFIX)。
briefing markdown と viz SVG、index.json をここから上げる。
"""

from __future__ import annotations

import boto3

from .. import config


class R2Client:
    def __init__(self) -> None:
        env = config.require(
            "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"
        )
        self._bucket = env["R2_BUCKET"]
        self._s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=env["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )

    def put(self, key: str, body: bytes, content_type: str) -> None:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=body, ContentType=content_type)

    def put_text(self, key: str, text: str, content_type: str) -> None:
        self.put(key, text.encode("utf-8"), content_type)

    def get_text(self, key: str) -> str | None:
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
        except self._s3.exceptions.NoSuchKey:
            return None
        return obj["Body"].read().decode("utf-8")
