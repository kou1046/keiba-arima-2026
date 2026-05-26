output "hostname" {
  value = local.hostname
}

output "access_application_id" {
  value = cloudflare_zero_trust_access_application.keiba.id
}
