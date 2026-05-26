# iwachan.dev zone の zone_id / account_id を core-iac の state から参照する。
# (zone / R2 bucket 本体は core-iac/cloudflare/iwachan-dev が管理。ここでは読むだけ。)
data "terraform_remote_state" "cloudflare_iwachan_dev" {
  backend = "s3"

  config = {
    bucket = "kou1046-general-bucket"
    key    = "core-iac/cloudflare/iwachan-dev/terraform.tfstate"
    region = "ap-northeast-1"
  }
}
