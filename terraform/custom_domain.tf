# keiba.iwachan.dev を keiba Worker (worker/) に bind する Custom Domain。
# Worker script 自体は worker/ の wrangler 管理 (src/worker.js)。
# 初回 apply の前に `cd worker && wrangler deploy` で Worker を作成しておく必要がある
# (chicken-and-egg、personal-llm と同じ運用)。
resource "cloudflare_workers_custom_domain" "keiba" {
  account_id = local.account_id
  zone_id    = local.zone_id
  hostname   = local.hostname
  service    = "keiba"
}
