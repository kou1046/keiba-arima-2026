# terraform (keiba.iwachan.dev フロント)

`keiba` Worker の Custom Domain と CF Access を管理する。Worker script 本体は
cf-gateway MCP / wrangler 管理で TF 対象外 (personal-llm と同じ方針)。

iwachan.dev zone / account は core-iac の remote state から参照 (`remote_state.tf`)。

## リソース

| file | resource | 備考 |
|---|---|---|
| `custom_domain.tf` | `cloudflare_workers_custom_domain.keiba` | keiba.iwachan.dev → keiba Worker |
| `access.tf` | `cloudflare_zero_trust_access_application.keiba` + `_policy.keiba_allow` | One-Time PIN, email allowlist |

## apply

```bash
export CLOUDFLARE_API_TOKEN=...   # workers + access + zone 権限
terraform init
terraform apply
```

Worker script は apply 前に deploy 済であること (cf-gateway 経由、`../worker` から)。

## 既存リソースの import (PoC で cf_api 先行作成したぶん)

PoC 段階で Custom Domain を cf-gateway の `cf_api` で先に作成済み。terraform が二重作成
しないよう、初回 apply の前に import して state に取り込む:

```bash
# id = <account_id>/<custom_domain_id>
terraform import cloudflare_workers_custom_domain.keiba \
  5c716b18b42d2a6825d14fe1b81e4989/321707bdc4cfd1522ed3325bf3f6ba6ea72da49d
```

import 後 `terraform plan` で差分が出なければ取り込み成功。CF Access は未作成なので
import 不要、apply で新規作成される (= ここで初めて keiba.iwachan.dev に認証が掛かる)。
