# Security Policy

## サポート対象

このリポジトリは個人運用の hobby project。サポート対象は `main` ブランチの最新コミットのみ。

## 脆弱性の報告

セキュリティ上の問題を見つけた場合、**Issue では報告しないでください**(他者が悪用するのを防ぐため)。

代わりに GitHub の **Private vulnerability reporting** を使ってください:

https://github.com/kou1046/keiba-arima-2026/security/advisories/new

または、メンテナにメールで直接連絡してください。返信は best-effort(週末を含めて 1 週間以内目安)。

## このプロジェクトのセキュリティ前提

- 競馬データ(`data/*.parquet`)は **public な情報**を集めたもので、機密性なし。
- AI が生成する分析メモは R2 に置かれ、`keiba.iwachan.dev` で **Cloudflare Access (One-Time PIN)** に保護される(email allowlist)。
- 認証 secret(`LLM_AUTH_TOKEN` 等)は **GitHub Actions secrets と Cloudflare secret store** のみで保管。コミットには含めない。
- repo を public 化しているが、デプロイ済み Worker / TF state には触れない。worker の bundle / TF apply は手元 / cf-gateway 経由でのみ実行。

## scope 外

- 個人 hobby project であり、SLA や定期的なセキュリティパッチは保証しない。
- フォーク / 派生物のセキュリティはフォーク側で管理してください。
