locals {
  api_only_user = {
    username      = "api-only-user-in-managed-tenant"
    roles = ["ROLE_SUPER_ADMIN"]
    api_only_user = true
  }
}
resource "cdo_msp_managed_tenant_users" "users" {
  tenant_uid = cdo_msp_managed_tenant.tenant.id
  users      = concat(var.users, [local.api_only_user])
}

