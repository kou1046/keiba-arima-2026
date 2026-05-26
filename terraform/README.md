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

import 後 `terraform plan` で差分が出なければ取り込み成功。

### CF Access (PoC で cf_api 作成済 → 削除して再作成推奨)

PoC で Access アプリも cf_api で作成済 (現在 keiba.iwachan.dev は One-Time PIN で保護中):

| resource | live id |
|---|---|
| application `keiba` | `ebe4ddb5-109c-431a-99fd-6762aed90de6` |
| policy `keiba email allowlist` | `9510117c-70a4-4c6c-ae83-033d2b1fd6a3` (inline / reusable=false, include=iwashiro0517@gmail.com) |

`access.tf` は **reusable policy** を別 resource で持ち app から参照する形なので、cf_api で作った
**inline policy** とはモデルが違う。import すると差分が暴れるため、Access は削除して terraform に
作り直すのが綺麗:

```bash
# 既存 Access app を削除 (cf-gateway cf_api or Dashboard)
#   DELETE /accounts/<account_id>/access/apps/ebe4ddb5-109c-431a-99fd-6762aed90de6
terraform apply   # access.tf が app + reusable policy を新規作成
```

削除〜apply の間だけ keiba.iwachan.dev が無認証になる点に注意 (データ未投入なら実害なし)。

### 代替: import せず削除して再作成

import を使わず、cf_api 作成分を一度消して terraform に作り直させてもよい。state が
綺麗になる代わり、削除〜apply の間 keiba.iwachan.dev が一瞬落ちる点だけ注意:

```bash
# 既存 Custom Domain を削除 (cf-gateway cf_api or CF Dashboard)
#   DELETE /accounts/<account_id>/workers/domains/321707bdc4cfd1522ed3325bf3f6ba6ea72da49d
terraform apply   # custom_domain + access をまとめて新規作成
```
