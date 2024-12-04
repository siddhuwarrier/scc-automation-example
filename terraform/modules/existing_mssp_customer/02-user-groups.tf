resource "cdo_msp_managed_tenant_user_groups" "user_groups" {
  tenant_uid  = cdo_msp_managed_tenant.tenant.id
  user_groups = var.user_groups
}