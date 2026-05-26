# keiba.iwachan.dev を CF Access で保護する。IdP を bind しないことで built-in の
# One-Time PIN (email OTP) が使える = 外部 IdP 不要・無料。email allowlist (var) で許可。
# R2 公開オブジェクトは必ずこの Access を手前に挟む構成 (Worker は Access JWT 検証済前提)。

resource "cloudflare_zero_trust_access_policy" "keiba_allow" {
  account_id = local.account_id
  name       = "keiba email allowlist"
  decision   = "allow"

  include = [for e in var.access_emails : { email = { email = e } }]
}

resource "cloudflare_zero_trust_access_application" "keiba" {
  zone_id          = local.zone_id
  name             = "keiba"
  domain           = local.hostname
  type             = "self_hosted"
  session_duration = var.access_session_duration

  # allowed_idps を指定しない → One-Time PIN を含む既定ログイン手段が利用可能。
  policies = [{
    id         = cloudflare_zero_trust_access_policy.keiba_allow.id
    precedence = 1
  }]
}
