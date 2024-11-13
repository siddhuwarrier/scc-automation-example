output "generated_tenant_name" {
  value = cdo_msp_managed_tenant.tenant.generated_name
}

output "tenant_region" {
  value = cdo_msp_managed_tenant.tenant.region
}

output "msp_managed_tenant_api_token" {
  value = cdo_msp_managed_tenant_user_api_token.tenant_api_token.api_token
  sensitive = true
}