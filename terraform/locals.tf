locals {
  account_id = data.terraform_remote_state.cloudflare_iwachan_dev.outputs.account_id
  zone_id    = data.terraform_remote_state.cloudflare_iwachan_dev.outputs.zone_id
  zone_name  = data.terraform_remote_state.cloudflare_iwachan_dev.outputs.zone_name

  hostname = "keiba.${local.zone_name}"
}
