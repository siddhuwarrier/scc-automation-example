import re
import re
import sys
from dataclasses import dataclass
from typing import List

import click
import questionary
from cdo_sdk_python import (
    ApiClient,
    Configuration,
    MSPApi,
    MspCreateTenantInput,
    CdoTransaction,
    UserInput,
    MspAddUsersToTenantInput,
)
from cdo_sdk_python.models.msp_managed_tenant import MspManagedTenant
from click_option_group import (
    optgroup,
    AllOptionGroup,
)
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskID

from parsers.scc_users_parser import SccUsersParser
from services.scc_credentials_service import SccCredentialsService
from services.transaction_service import TransactionService
from utils.region_mapping import supported_regions
from validators.users_csv_validator import UsersCsvValidator


@dataclass
class CmdlineArgs:
    tenant_name: str
    display_name: str
    users_csv_file: str
    region: str
    api_token: str


def validate_user_csv_file(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> str:
    if value:
        validator = UsersCsvValidator(value)
        if not validator.validate():
            raise click.BadParameter(f"CSV file {value} is invalid.")
    return value


def create_tenant(
    tenant_name: str, display_name: str, api_client: ApiClient
) -> MspManagedTenant:
    msp_api: MSPApi = MSPApi(api_client)
    transaction_service: TransactionService = TransactionService(api_client)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        create_tenant_task_id: TaskID = progress.add_task(
            "Creating tenant...", start=True
        )
        transaction: CdoTransaction = msp_api.create_tenant(
            MspCreateTenantInput(
                **{"tenant_name": tenant_name, "display_name": display_name}
            )
        )
        try:
            finished_transaction: CdoTransaction = (
                transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=transaction.transaction_uid
                )
            )
            msp_managed_tenant: MspManagedTenant = msp_api.get_msp_managed_tenant(
                tenant_uid=finished_transaction.entity_uid
            )
        except RuntimeError as e:
            progress.update(task_id=create_tenant_task_id, description=f"Error:{e}")
            sys.exit(1)
        finally:
            progress.stop_task(task_id=create_tenant_task_id)

    return msp_managed_tenant


def create_users(
    users: List[UserInput], msp_managed_tenant: MspManagedTenant, api_client: ApiClient
) -> None:
    msp_api = MSPApi(api_client)
    transaction_service = TransactionService(api_client)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        add_users_to_tenant_task_id: TaskID = progress.add_task(
            f"Creating {len(users)} users in tenant {msp_managed_tenant.display_name} ({msp_managed_tenant.region})...",
            start=True,
        )
        transaction: CdoTransaction = msp_api.add_users_to_tenant_in_msp_portal(
            msp_managed_tenant.uid, MspAddUsersToTenantInput(**{"users": users})
        )
        try:
            transaction_service.wait_for_transaction_to_finish(
                transaction_uid=transaction.transaction_uid
            )
        except RuntimeError as e:
            progress.update(
                task_id=add_users_to_tenant_task_id, description=f"Error:{e}"
            )
            sys.exit(1)
        finally:
            progress.stop_task(task_id=add_users_to_tenant_task_id)


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
) -> None:
    args: CmdlineArgs = CmdlineArgs(
        tenant_name=tenant_name,
        display_name=display_name,
        users_csv_file=users_csv_file,
        region=region,
        api_token=api_token,
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

    with ApiClient(Configuration(host=base_url, access_token=api_token)) as api_client:
        msp_managed_tenant: MspManagedTenant = create_tenant(
            tenant_name=args.tenant_name,
            display_name=args.display_name,
            api_client=api_client,
        )
        console.print("[green]Tenant created successfully[/green]")
        create_users(
            users=users, msp_managed_tenant=msp_managed_tenant, api_client=api_client
        )
        console.print("[green]Users added to tenant successfully[/green]")


if __name__ == "__main__":
    main()
