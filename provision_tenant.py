import re
from dataclasses import dataclass
from typing import List

import click
import questionary
from cdo_sdk_python import ApiClient, Configuration, UserInput, MspManagedTenant
from click_option_group import optgroup, AllOptionGroup
from rich.console import Console

from parsers.scc_users_parser import SccUsersParser
from services.cdfmc_api_service import CdFmcApiService
from services.msp_api_service import MspApiService
from services.scc_credentials_service import SccCredentialsService
from utils.region_mapping import supported_regions
from validators.users_csv_validator import UsersCsvValidator


@dataclass
class CmdlineArgs:
    tenant_name: str
    display_name: str
    users_csv_file: str
    region: str
    api_token: str
    provision_cdfmc: str


def validate_user_csv_file(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> str:
    if value:
        validator = UsersCsvValidator(value)
        if not validator.validate():
            raise click.BadParameter(f"CSV file {value} is invalid.")
    return value


@click.command(
    help="Create a new MSSP-managed tenant. You need a super-admin API token generated using the Cisco Security Cloud Control MSSP portal to use this script."
)
@click.option(
    "--tenant-name", type=str, help="The tenant name (must match [a-zA-Z0-9-_]{1,50})."
)
@click.option("--display-name", type=str, help="The display name.")
@click.option(
    "--users-csv-file",
    type=str,
    callback=validate_user_csv_file,
    help="Path to the CSV file with user data. The CSV file must contain 'username', 'role', and 'api_only_user' columns. 'username' must be an email address if 'api_only_user' is false, and not an email address if 'api_only_user' is true. 'role' must be one of 'ROLE_SUPER_ADMIN', 'ROLE_ADMIN', 'ROLE_READ_ONLY', 'ROLE_EDIT_ONLY', 'ROLE_DEPLOY_ONLY', or 'ROLE_VPN_SESSION_MANAGER'.",
)
@click.option(
    "--provision-cdfmc",
    type=click.Choice(["yes", "no"]),
    help="Provision a cdFMC (yes or no).",
)
@optgroup.group("API Credentials", cls=AllOptionGroup)
@optgroup.option(
    "--region",
    help="The region for the API.",
    type=click.Choice(supported_regions),
)
@optgroup.option("--api-token", type=str, help="The API token.")
def main(
    tenant_name: str,
    display_name: str,
    users_csv_file: str,
    region: str,
    api_token: str,
    provision_cdfmc: str,
) -> None:
    args: CmdlineArgs = CmdlineArgs(
        tenant_name=tenant_name,
        display_name=display_name,
        users_csv_file=users_csv_file,
        region=region,
        api_token=api_token,
        provision_cdfmc=provision_cdfmc,
    )
    credentials_service = SccCredentialsService(
        region=args.region, api_token=args.api_token
    )
    credentials_service.load_or_prompt_credentials()
    scc_users_parser = SccUsersParser(args.users_csv_file)
    console = Console()
    credentials_service.load_or_prompt_credentials()
    api_token, base_url = credentials_service.get_credentials()

    if not args.tenant_name:
        args.tenant_name = questionary.text(
            message="Enter the tenant name (must match [a-zA-Z0-9-_]{1,50}):",
            validate=lambda text: bool(re.match(r"^[a-zA-Z0-9-_]{1,50}$", text)),
        ).ask()
    if not args.display_name:
        args.display_name = questionary.text("Enter the display name:").ask()
    users: List[UserInput] = scc_users_parser.get_users()
    api_only_user_name = f"{args.tenant_name}-api-only-user"
    console.print(
        f"[yellow]Adding API-only user {api_only_user_name} to configure the newly provisioned tenant... [/yellow]"
    )
    api_only_user = UserInput(
        username=api_only_user_name, role="ROLE_SUPER_ADMIN", api_only_user=True
    )
    users.append(api_only_user)

    if not args.provision_cdfmc:
        args.provision_cdfmc = questionary.text(
            message="Do you want to provision a cdFMC? [yes/no]",
            default="no",
            validate=lambda text: text.lower() in ["yes", "no"],
        ).ask()

    with ApiClient(Configuration(host=base_url, access_token=api_token)) as api_client:
        msp_api_service = MspApiService(api_client=api_client)
        msp_managed_tenant: MspManagedTenant = msp_api_service.create_tenant(
            tenant_name=args.tenant_name,
            display_name=args.display_name,
        )
        console.print(
            f"[green]Tenant {msp_managed_tenant.display_name} (UID: {msp_managed_tenant.uid})created successfully[/green]"
        )
        msp_api_service.create_users(users=users, msp_managed_tenant=msp_managed_tenant)
        console.print("[green]Users added to tenant successfully[/green]")
        msp_managed_tenant_api_token = (
            msp_api_service.generate_managed_tenant_api_token(
                msp_managed_tenant=msp_managed_tenant, username=api_only_user_name
            )
        )
        msp_api_service.provision_cdfmc_on_msp_managed_tenant(
            msp_managed_tenant=msp_managed_tenant,
            msp_managed_tenant_api_token=msp_managed_tenant_api_token,
            should_wait_for_cdfmc_to_be_active=True,
        )
        console.print("[green]cdFMC provisioned successfully[/green]")
        cdfmc_api_service = CdFmcApiService(
            api_client=ApiClient(
                Configuration(host=base_url, access_token=msp_managed_tenant_api_token)
            )
        )
        access_policy_uid = cdfmc_api_service.create_default_access_policy()
        cdfmc_api_service.block_gambling(access_policy_uid=access_policy_uid)
        console.print(
            f"[green]MSP access policy with UID {access_policy_uid} created successfully[/green]"
        )


if __name__ == "__main__":
    main()
