output "api_token" {
  value     = module.woomera_enterprises.msp_managed_tenant_api_token
  sensitive = true
}