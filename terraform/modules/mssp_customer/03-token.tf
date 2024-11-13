locals {
  api_only_user_id = [
    for user in cdo_msp_managed_tenant_users.users.users : user.id
    if user.username == local.api_only_user.username
  ][
  0
  ]
}

resource "cdo_msp_managed_tenant_user_api_token" "tenant_api_token" {
  user_uid   = local.api_only_user_id
  tenant_uid = cdo_msp_managed_tenant.tenant.id
}