import re
from dataclasses import dataclass
from typing import List, Tuple

import click
import questionary
from cdo_sdk_python import (
    ZtpOnboardingInput,
    ApiClient,
    Configuration,
    MspManagedTenant,
    FtdCreateOrUpdateInput,
    Device,
)
from click_option_group import optgroup, AllOptionGroup, MutuallyExclusiveOptionGroup
from rich.console import Console

from parsers.ftd_parser import FtdParser
from parsers.ftd_ztp_parser import FtdZtpParser
from services.inventory_api_service import InventoryApiService
from services.msp_api_service import MspApiService
from services.scc_credentials_service import SccCredentialsService
from utils.region_mapping import supported_regions
from validators.ftd_csv_validator import FtdCsvValidator
from validators.ftd_ztp_csv_validator import FtdZtpCsvValidator


@dataclass
class CmdlineArgs:
    tenant_uid: str
    fmc_access_policy_uid: str
    username: str
    ftd_csv_file: str
    ftd_ztp_csv_file: str
    api_token: str
    region: str


UUID_REGEX = re.compile(
    r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
)


def validate_uuid(ctx: click.Context, param: click.Parameter, value: str) -> str | None:
    if value is not None and not UUID_REGEX.match(value):
        raise click.BadParameter(f"{param.name} must be a valid UUID.")
    return value


def validate_ftd_csv_file(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> str:
    if value:
        validator = FtdCsvValidator(value)
        if not validator.validate():
            raise click.BadParameter(f"CSV file {value} is invalid.")
    return value


def validate_ztp_ftd_csv_file(
    _ctx: click.Context, _param: click.Parameter, value: str
) -> str:
    if value:
        validator = FtdZtpCsvValidator(value)
        if not validator.validate():
            raise click.BadParameter(f"CSV file {value} is invalid.")
    return value


@click.command(
    help="Onboard FTDs to an MSP managed tenant. You need a super-admin API token generated using the Cisco Security Cloud Control MSSP portal to use this script."
)
@click.option(
    "--tenant-uid",
    type=str,
    callback=validate_uuid,
    help="The UID of the MSP-managed tenant to onboard the devices to.",
)
@click.option(
    "--fmc-access-policy-uid",
    type=str,
    callback=validate_uuid,
    help="The UID of the access policy to apply to this device when onboarded.",
)
@click.option(
    "--username",
    type=str,
    help="The name of the API-only user on the MSP-managed tenant. Defaults to <tenant-name>-api-only-user.",
)
@optgroup.group("FTD Onboarding type", cls=MutuallyExclusiveOptionGroup)
@optgroup.option(
    "--ftd-csv-file",
    type=str,
    callback=validate_ftd_csv_file,
    help="Path to the CSV file with FTD information. The CSV file should contain the FTD address, username, password, licenses, and performance tier if the FTD is virtual.",
)
@optgroup.option(
    "--ftd-ztp-csv-file",
    type=str,
    callback=validate_ztp_ftd_csv_file,
    help="Path to the CSV file with FTD information. The CSV file should contain the FTD name, serial number, admin password, and licenses",
)
@optgroup.group("API Credentials", cls=AllOptionGroup)
@optgroup.option(
    "--region",
    help="The region for the API.",
    type=click.Choice(supported_regions),
)
@optgroup.option("--api-token", type=str, help="The API token.")
def main(
    tenant_uid: str,
    username: str,
    ftd_csv_file: str,
    ftd_ztp_csv_file: str,
    region: str,
    api_token: str,
    fmc_access_policy_uid: str,
) -> None:
    console = Console()
    args: CmdlineArgs = CmdlineArgs(
        tenant_uid=tenant_uid,
        username=username,
        ftd_csv_file=ftd_csv_file,
        ftd_ztp_csv_file=ftd_ztp_csv_file,
        region=region,
        api_token=api_token,
        fmc_access_policy_uid=fmc_access_policy_uid,
    )
    credentials_service = SccCredentialsService(
        region=args.region, api_token=args.api_token
    )
    credentials_service.load_or_prompt_credentials()
    api_token, base_url = credentials_service.get_credentials()
    if not args.tenant_uid:
        args.tenant_uid = questionary.text(
            message="Enter the MSP-managed tenant UUID, it should be associated with the MSP portal (must match [a-zA-Z0-9-_]{1,50}):",
            validate=lambda text: bool(re.match(UUID_REGEX, text)),
        ).ask()
    if not args.fmc_access_policy_uid:
        args.fmc_access_policy_uid = questionary.text(
            message="Enter the access policy UUID to apply to each onboarded device:",
            validate=lambda text: bool(re.match(UUID_REGEX, text)),
        ).ask()

    ztp_onboarding_inputs: List[ZtpOnboardingInput] = FtdZtpParser(
        ftd_ztp_csv_file=args.ftd_ztp_csv_file,
        fmc_access_policy_uid=args.fmc_access_policy_uid,
    ).get_ztp_onboarding_inputs()

    ftd_onboarding_inputs: List[FtdCreateOrUpdateInput] = FtdParser(
        ftd_csv_file=args.ftd_csv_file,
        fmc_access_policy_uid=args.fmc_access_policy_uid,
    ).get_ftds_to_onboard()

    with ApiClient(
        Configuration(host=base_url, access_token=api_token)
    ) as msp_api_client:
        msp_api_service = MspApiService(api_client=msp_api_client)
        msp_managed_tenant: MspManagedTenant = (
            msp_api_service.get_managed_tenant_by_uid(tenant_uid=args.tenant_uid)
        )
        msp_managed_tenant_api_token: str = (
            msp_api_service.generate_managed_tenant_api_token(
                msp_managed_tenant=msp_managed_tenant,
                username=(
                    args.username
                    if args.username is not None
                    else f"{msp_managed_tenant.name.replace("CDO_", "").split("__")[0]}-api-only-user"
                ),
            )
        )
        console.print(
            f"[green]Generated API token for {msp_managed_tenant.name} (UID: {msp_managed_tenant.uid})[/green]"
        )

    with ApiClient(
        Configuration(host=base_url, access_token=msp_managed_tenant_api_token)
    ) as managed_tenant_api_client:
        inventory_api_service = InventoryApiService(
            api_client=managed_tenant_api_client
        )
        for ztp_onboarding_input in ztp_onboarding_inputs:
            ztp_device: Device = inventory_api_service.onboard_ftd_ztp_device(
                ztp_onboarding_input=ztp_onboarding_input
            )
            console.print(
                f"[green]Onboarded FTD {ztp_device.name} (UID: {ztp_device.uid})[/green]"
            )
        for ftd_onboarding_input in ftd_onboarding_inputs:
            device: Device = inventory_api_service.onboard_ftd_device(
                ftd_input=ftd_onboarding_input
            )
            console.print(
                f"[green]Onboarded FTD {device.name} (UID: {device.uid})[/green]"
            )


if __name__ == "__main__":
    main()
