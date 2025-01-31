from typing import List

import click
import questionary
from cdo_sdk_python import (
    ApiClient,
    Configuration,
    Device,
    FtdVersion,
)
from click_option_group import AllOptionGroup, optgroup
from rich.console import Console

from services.device_upgrade_api_service import DeviceUpgradeApiService
from services.inventory_api_service import InventoryApiService
from services.scc_credentials_service import SccCredentialsService
from services.transaction_service import TransactionService
from utils.region_mapping import supported_regions


def select_ftd(api_client: ApiClient) -> str:
    inventory_api_service = InventoryApiService(api_client)
    devices: List[Device] = inventory_api_service.get_devices(
        q="deviceType:CDFMC_MANAGED_FTD AND connectivityState:ONLINE"
    )
    device_names = [f"{device.name} ({device.software_version})" for device in devices]
    selected_device = questionary.select("Select a device:", choices=device_names).ask()
    return next(
        device.uid
        for device in devices
        if device.name == selected_device.split(" (")[0]
    )


def select_ftd_version(ftd_uid: str, api_client: ApiClient) -> FtdVersion:
    device_upgrade_service = DeviceUpgradeApiService(api_client)
    ftd_versions: List[FtdVersion] = device_upgrade_service.get_compatible_ftd_versions(
        ftd_uid
    )
    software_versions: List[str] = [
        (
            f"{ftd_version.software_version}*"
            if ftd_version.is_suggested_version
            else ftd_version.software_version
        )
        for ftd_version in ftd_versions
    ]

    selected_software_version = questionary.select(
        "Select FTD version (suggested versions are marked with a *)",
        choices=software_versions,
    ).ask()
    return next(
        ftd_version
        for ftd_version in ftd_versions
        if ftd_version.software_version == selected_software_version.split("*")[0]
    )


@click.group()
@optgroup.group("API Credentials", cls=AllOptionGroup)
@optgroup.option(
    "--region",
    help="The region for the API.",
    type=click.Choice(supported_regions),
)
@optgroup.option("--api-token", type=str, help="The API token.")
@click.pass_context
def cli(ctx: any, api_token: str, region: str) -> None:
    credentials_service = SccCredentialsService(region=region, api_token=api_token)
    credentials_service.load_or_prompt_credentials()
    retrieved_api_token, base_url = credentials_service.get_credentials()
    ctx.obj["base_url"] = base_url
    ctx.obj["api_token"] = retrieved_api_token


@click.command(name="list-versions")
@click.option(
    "--ftd-uid",
    help="The UID of the FTD to list compatible versions for.",
    type=str,
    required=False,
)
@click.pass_context
def list_versions(ctx: any, ftd_uid: str) -> None:
    """Retrieve the list of compatible versions for the given FTD UID."""
    # Add logic to retrieve and display the list of compatible versions
    with ApiClient(
        Configuration(host=ctx.obj["base_url"], access_token=ctx.obj["api_token"])
    ) as api_client:
        if ftd_uid is None:
            ftd_uid = select_ftd(api_client)

        device_upgrade_service = DeviceUpgradeApiService(api_client)
        ftd_versions: List[FtdVersion] = (
            device_upgrade_service.get_compatible_ftd_versions(ftd_uid)
        )
        device_upgrade_service.print_ftd_versions(ftd_versions)


@click.command(name="upgrade")
@click.option(
    "--ftd-uid", help="The UID of the FTD to upgrade.", type=str, required=False
)
@click.option(
    "--upgrade-package-uid",
    help="The UID of the upgrade package to use to perform the FTD upgrade.",
    type=str,
    required=False,
)
@click.pass_context
def upgrade(ctx: any, ftd_uid: str, upgrade_package_uid: str) -> None:
    """Trigger an upgrade for the given FTD UID using the specified upgrade package UID."""
    with ApiClient(
        Configuration(host=ctx.obj["base_url"], access_token=ctx.obj["api_token"])
    ) as api_client:
        if ftd_uid is None:
            ftd_uid = select_ftd(api_client)
        if upgrade_package_uid is None:
            ftd_version = select_ftd_version(ftd_uid, api_client)
            upgrade_package_uid = ftd_version.upgrade_package_uid

        device_upgrade_service = DeviceUpgradeApiService(api_client)
        device_upgrade_service.upgrade_ftd(ftd_uid=ftd_uid, ftd_version=ftd_version)
        Console().print(
            f"Upgraded FTD with UID: {ftd_uid} to version {ftd_version.software_version} using upgrade package UID: {upgrade_package_uid}"
        )


cli.add_command(list_versions)
cli.add_command(upgrade)

if __name__ == "__main__":
    cli(obj={})
