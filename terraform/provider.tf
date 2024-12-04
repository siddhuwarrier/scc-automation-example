terraform {
  required_providers {
    cdo = {
      source = "CiscoDevNet/cdo"
      version = "3.2.0"
    }
  }
}

provider "cdo" {
  base_url = var.base_url
  api_token = var.mssp_portal_api_token
}