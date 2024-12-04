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
  mssp_user_groups = [
    {
      group_identifier = "siddhusmsp-developers"
      issuer_url       = "https://okta.com/siddhusmsp"
      name             = "MSP developers"
      role             = "ROLE_SUPER_ADMIN"
    },
    {
      group_identifier = "siddhusmsp-managers"
      issuer_url       = "https://okta.com/siddhusmsp"
      name             = "MSP managers"
      role             = "ROLE_ADMIN"
    }
  ]
  bangers_and_cash_users = [
    {
      username      = "john.doe@bangers-and-cash.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "jane.smith@bangers-and-cash.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "michael.brown@bangers-and-cash.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    }
  ]
  bangers_and_cash_user_groups = [
    {
      group_identifier = "bangers-and-cash-developers"
      issuer_url       = "https://okta.com/bangers"
      name             = "Bangers and Cash developers"
      role             = "ROLE_READ_ONLY"
    },
    {
      group_identifier = "bangers-and-cash-managers"
      issuer_url       = "https://okta.com/bangers"
      name             = "Bangers and Cash managers"
      role             = "ROLE_READ_ONLY"
    }
  ]
  patriotic_fried_chicken_penge_users = [
    {
      username      = "bindi.irwin@pfc-penge.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "koori.jones@pfc-penge.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    },
    {
      username      = "yindi.smith@pfc-penge.co.uk"
      roles = ["ROLE_READ_ONLY"]
      api_only_user = false
    }
  ]
  patriotic_fried_chicken_penge_user_groups = [
    {
      group_identifier = "penge-managers"
      issuer_url       = "https://okta.com/penge-pfc"
      name             = "Patriotic Fried Chicken Managers"
      role             = "ROLE_READ_ONLY"
    }
  ]
  mgd_tenant_api_token = "eyJraWQiOiIwIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOiIwIiwicm9sZXMiOlsiUk9MRV9TVVBFUl9BRE1JTiJdLCJpc3MiOiJpdGQiLCJjbHVzdGVySWQiOiIxIiwic3ViamVjdFR5cGUiOiJ1c2VyIiwiY2xpZW50X2lkIjoiYXBpLWNsaWVudCIsInBhcmVudElkIjoiMWRmMjA3MmYtMDU3MS00ZDdiLTgzNDMtMzVhMzM3NWJlMWM2Iiwic2NvcGUiOlsidHJ1c3QiLCJyZWFkIiwiMWRmMjA3MmYtMDU3MS00ZDdiLTgzNDMtMzVhMzM3NWJlMWM2Iiwid3JpdGUiXSwiaWQiOiJhOWFhYTM5Yy04NDlhLTQzOGYtYWE0Yi0yZjk4M2YyYzAxOGEiLCJleHAiOjM4ODA4MDY5NzMsImlhdCI6MTczMzMyMzM4NiwianRpIjoiZmM0ZDVlMzgtZDNiMC00NTI5LTg5NzItMWM2OGFlNTljYTBlIn0.aPmbpvqeqZu8gWiBpMrl8uETMiOhfWDGhP4drPB0CYmzy5nJJ6pzkgUYAtf8jVD1dBqaK6xAo7wlAKqVOuRXeFubFdvpB5xBBsxLS4RdHyQcW9yLkTqTMSStczYNpAQWfId0ezJjcXmbWB6ez7Z02_TWDnZ3vJdB4MJzFM03sMcJGoAud77W4rvlqd218_-WvlhzISGGCpcNAKLHKB61aabbrqTpUZ5K4l_kVgWaR3k4edd0MpUZXXk4OuMdSC7bNgPPDLQVEqTneBDWI9wfHxBNECFmNWSgHqoJC5OSavPh09pPHmB2pr-0S4ZgJtq6R-1bYdwuU2kVrymcS0ikWQ"
}

module "bangers_and_cash" {
  source              = "./modules/mssp_customer"
  tenant_name         = "bangers-and-cash-ltd"
  tenant_display_name = "Bangers and Cash Ltd"
  users = concat(local.bangers_and_cash_users, local.mssp_users)
  user_groups = concat(local.bangers_and_cash_user_groups, local.mssp_user_groups)
}

module "patriotic_fried_chicken_penge" {
  source = "./modules/existing_mssp_customer"
  mgd_tenant_api_token = local.mgd_tenant_api_token
  user_groups = concat(local.patriotic_fried_chicken_penge_user_groups, local.mssp_user_groups)
}