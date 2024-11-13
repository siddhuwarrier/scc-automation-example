locals {
  mssp_users = [
    {
      username      = "rahul.sharma@siddhusmsp.com"
      roles = ["ROLE_SUPER_ADMIN"]
      api_only_user = false
    },
    {
      username      = "aisha.khan@siddhusmsp.com"
      roles = ["ROLE_SUPER_ADMIN"]
      api_only_user = false
    },
    {
      username      = "vijay.patel@siddhusmsp.com"
      roles = ["ROLE_SUPER_ADMIN"]
      api_only_user = false
    }
  ]
  woomera_enterprises_users = [
    {
      username      = "john.doe@woomera.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "jane.smith@woomera.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "michael.brown@woomera.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    }
  ]
  wiradjuri_networks_users = [
    {
      username      = "bindi.irwin@wiradjuri.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "koori.jones@wiradjuri.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "yindi.smith@wiradjuri.com"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    }
  ]
}

module "woomera_enterprises" {
  source              = "./modules/mssp_customer"
  tenant_name         = "woomera_enterprises"
  tenant_display_name = "Woomera Enterprises"
  users = concat(local.woomera_enterprises_users, local.mssp_users)
}

module "wiradjuri_networks" {
  source              = "./modules/mssp_customer"
  tenant_name         = "wiradjuri_networks"
  tenant_display_name = "Wiradjuri Networks"
  users = concat(local.wiradjuri_networks_users, local.mssp_users)
  # Wait for previous tenant to be created before creating this one, to avoid falling afoul of SCC rate limits
  depends_on = [module.woomera_enterprises]
}

module "woomera_enterprises_resources" {
  source                   = "./modules/mssp_tenant_resources"
  scc_base_url             = var.base_url
  managed_tenant_api_token = module.woomera_enterprises.msp_managed_tenant_api_token
  ftds = [
    {
      name             = "wagga-wagga"
      licenses = ["BASE", "MALWARE", "THREAT", "URLFilter"]
      ssh_address      = "10.84.31.131"
      ssh_port         = "1236"
      username         = "admin"
      password         = "BlueSkittles123!!"
      virtual          = true
      performance_tier = "FTDv5"
    }
  ]
}

module "wiradjuri_networks_resources" {
  source                   = "./modules/mssp_tenant_resources"
  scc_base_url             = var.base_url
  managed_tenant_api_token = module.wiradjuri_networks.msp_managed_tenant_api_token
  ftds = [
    {
      name             = "Uluru"
      licenses = ["BASE", "MALWARE", "THREAT", "URLFilter"]
      ssh_address      = "10.84.31.131"
      ssh_port         = "1237"
      username         = "admin"
      password         = "BlueSkittles123!!"
      virtual          = true
      performance_tier = "FTDv5"
    }
  ]
}
