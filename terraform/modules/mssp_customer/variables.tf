variable "tenant_name" {
  description = "The name of the tenant to create"
  validation {
    condition = can(regex("^[a-zA-Z0-9-_]{1,50}$", var.tenant_name))
    error_message = "The tenant_name must match the regex [a-zA-Z0-9-_]{1,50}."
  }
  type = string
}

variable "tenant_display_name" {
  description = "The display name of the tenant to create"
  type        = string
}

variable "users" {
  description = <<EOF
A list of users, where each user has a username, roles, and
a boolean indicating if it is an API-only user.
EOF
  type = list(object({
    username      = string
    roles = list(string)
    api_only_user = bool
  }))
  validation {
    condition = alltrue([
      for user in var.users : alltrue([
        for role in user.roles : length(user.roles) == 1 && contains([
        "ROLE_ADMIN", "ROLE_SUPER_ADMIN", "ROLE_READ_ONLY", "ROLE_VPN_SESSION_MANAGER",
        "ROLE_DEPLOY_ONLY", "ROLE_EDIT_ONLY"
      ], role)
        ])
    ])
    error_message = "Each user must have exactly one role, and it must be one of ROLE_ADMIN, ROLE_SUPER_ADMIN, ROLE_READ_ONLY, ROLE_VPN_SESSION_MANAGER, ROLE_DEPLOY_ONLY, or ROLE_EDIT_ONLY."
  }
}