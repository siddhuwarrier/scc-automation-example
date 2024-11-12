Example Terraform code to manage customer tenants using Security Cloud Control, the MSSP portal,
and cloud-delivered Firewall Management Center (cdFMC).

## Prerequisites
- Terraform 1.3.9 or later
- Access to an Security Cloud Control MSSP portal
  - Talk to your sales team or TAC to get access to it.

## Getting started
- Generate an API token for the MSSP portal
  - See https://docs.defenseorchestrator.com/c_api-tokens.html
- Copy terraform.tfvars.sample to terraform.tfvars and fill in the required variables.
- Run `terraform init` to download the required providers.
