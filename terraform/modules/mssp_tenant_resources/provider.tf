terraform {
  required_providers {
    cdo = {
      source  = "ciscodevnet/cdo"
      version = "3.0.2"
    }
    fmc = {
      source  = "ciscodevnet/fmc"
      version = "1.5.2"
    }
  }
}

provider "cdo" {
  alias     = "msp_managed_tenant"
  base_url  = var.scc_base_url
  api_token = var.managed_tenant_api_token
}