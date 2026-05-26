terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }

  # state は core-iac と同じ S3 bucket に置く (運用 bucket を 1 つに集約)。
  backend "s3" {
    bucket = "kou1046-general-bucket"
    key    = "keiba-arima-2026/terraform/terraform.tfstate"
    region = "ap-northeast-1"
  }
}

# Cloudflare provider は AWS のような default_tags を持たないため付与なし
# (provider-tags は AWS 向けルール)。CLOUDFLARE_API_TOKEN は env で渡す。
provider "cloudflare" {}
