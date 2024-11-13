resource "cdo_cdfmc" "msp_managed_tenant_cdfmc" {
  # use the MSP-managed tenant provider
  provider = cdo.msp_managed_tenant
}

provider "fmc" {
  fmc_host          = cdo_cdfmc.msp_managed_tenant_cdfmc.hostname
  is_cdfmc          = true
  cdo_token         = var.managed_tenant_api_token
  cdfmc_domain_uuid = cdo_cdfmc.msp_managed_tenant_cdfmc.domain_uuid
}

resource "fmc_url_objects" "bet365" {
  name        = "bet-365"
  url         = "https://www.bet365.com/"
  description = "Bet365"
}

resource "fmc_url_objects" "paddypower" {
  name        = "paddy-power"
  url         = "https://www.paddypower.com/"
  description = "PaddyPower"
}

resource "fmc_url_object_group" "gambling" {
  name        = "Gambling"
  description = "Gambling websites"
  objects {
    id   = fmc_url_objects.bet365.id
    type = fmc_url_objects.bet365.type
  }
  objects {
    id   = fmc_url_objects.paddypower.id
    type = fmc_url_objects.paddypower.type
  }
  literals {
    url = "https://www.betfair.com"
  }
}

data "fmc_network_objects" "any-ipv4" {
  name = "any-ipv4"
}

resource "fmc_access_policies" "msp_access_policy" {
  name = "MSP access policy"
  default_action = "block"
  # wait for cdFMC to be provisioned before creating the access policy
  depends_on = [cdo_cdfmc.msp_managed_tenant_cdfmc]
}

resource "fmc_access_rules" "block_gambling_access_rule" {
  acp     = fmc_access_policies.msp_access_policy.id
  action  = "BLOCK"
  enabled = true
  name    = "Gambling"
  source_networks {
    source_network {
      id   = data.fmc_network_objects.any-ipv4.id
      type = data.fmc_network_objects.any-ipv4.type
    }
  }
  urls {
    url {
      id = fmc_url_object_group.gambling.id
      type = fmc_url_object_group.gambling.type
    }
  }
}