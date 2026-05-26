variable "access_emails" {
  type        = list(string)
  description = "keiba.iwachan.dev を閲覧できる email allowlist (自分 + 友人)。CF Access が One-Time PIN で認証。"
  default     = ["kosuke-iwashiro@c-fo.com"]
}

variable "access_session_duration" {
  type        = string
  description = "CF Access セッションの有効期間。"
  default     = "168h" # 1 週間
}
