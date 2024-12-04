variable "mgd_tenant_api_token" {
  description = "The API token for the Managed tenant. This is used to authenticate with Security Cloud Control."
  validation {
    condition = can(regex("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$", var.mgd_tenant_api_token))
    error_message = "The mssp_portal_api_token must be a valid JWT token."
  }
}

variable "user_groups" {
  description = <<EOF
A list of user groups, where each user group has a username, roles, and
a boolean indicating if it is an API-only user.
EOF
  type = list(object({
    group_identifier = string
    issuer_url       = string
    name             = string
    role             = string
  }))
  validation {
    condition = alltrue([
      for user in var.user_groups : contains([
        "ROLE_ADMIN", "ROLE_SUPER_ADMIN", "ROLE_READ_ONLY", "ROLE_VPN_SESSION_MANAGER",
        "ROLE_DEPLOY_ONLY", "ROLE_EDIT_ONLY"
      ], user.role)
    ])
    error_message = "Each user group must have a role, that is one of ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_READ_ONLY, ROLE_VPN_SESSION_MANAGER, ROLE_DEPLOY_ONLY, or ROLE_EDIT_ONLY."
  }
}