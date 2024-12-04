variable "base_url" {
  description = "The base URL for Security Cloud Control. This is the URL you access Security Cloud Control from."
  type        = string
  validation {
    condition = contains([
      "https://aus.manage.security.cisco.com", "https://eu.manage.security.cisco.com",
      "https://us.manage.security.cisco.com", "https://in.manage.security.cisco.com",
      "https://apj.manage.security.cisco.com", "https://staging.manage.security.cisco.com"
    ], var.base_url)
    error_message = "The base_url must be one of the following: https://aus.manage.security.cisco.com, https://eu.manage.security.cisco.com, https://us.manage.security.cisco.com, https://in.manage.security.cisco.com, https://apj.manage.security.cisco.com."
  }
}

variable "mssp_portal_api_token" {
  description = "The API token for the MSSP Portal. This is used to authenticate with Security Cloud Control."
  validation {
    condition = can(regex("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$", var.mssp_portal_api_token))
    error_message = "The mssp_portal_api_token must be a valid JWT token."
  }
}