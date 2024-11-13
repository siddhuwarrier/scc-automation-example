resource "cdo_msp_managed_tenant" "tenant" {
  name         = var.tenant_name
  display_name = var.tenant_display_name
}

