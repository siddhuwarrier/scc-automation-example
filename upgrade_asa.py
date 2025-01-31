from typing import List

import click
import questionary
from cdo_sdk_python import (
    ApiClient,
    Configuration,
    Device,
    AsaCompatibleVersion,
    UpgradeAsaDeviceInput,
)
from click_option_group import AllOptionGroup, optgroup
from rich.console import Console

from services.device_upgrade_api_service import DeviceUpgradeApiService
from services.inventory_api_service import InventoryApiService
from services.scc_credentials_service import SccCredentialsService
from utils.region_mapping import supported_regions


def select_asa(api_client: ApiClient) -> str:
    inventory_api_service = InventoryApiService(api_client)
    devices: List[Device] = inventory_api_service.get_devices(
        q="deviceType:ASA AND connectivityState:ONLINE"
    )
    device_names = [f"{device.name} ({device.software_version})" for device in devices]
    selected_device = questionary.select("Select a device:", choices=device_names).ask()
    return next(
        device.uid
        for device in devices
        if device.name == selected_device.split(" (")[0]
    )


def select_asa_version(asa_uid: str, api_client: ApiClient) -> UpgradeAsaDeviceInput:
    device_upgrade_service = DeviceUpgradeApiService(api_client)
    asa_versions: List[AsaCompatibleVersion] = (
        device_upgrade_service.get_compatible_asa_versions(asa_uid)
    )
    if len(asa_versions) == 0:
        raise RuntimeError("No compatible versions found for the selected ASA device.")
    software_versions: List[str] = [
        f"{asa_version.software_version} (ASDM: {asa_version.asdm_version})"
        for asa_version in asa_versions
    ]

    selected_software_version = questionary.select(
        "Select ASA version",
        choices=software_versions,
    ).ask()

    selected_asa_version: AsaCompatibleVersion = None
    for asa_version in asa_versions:
        strrep = f"{asa_version.software_version} (ASDM: {asa_version.asdm_version})"
        if strrep == selected_software_version:
            selected_asa_version = asa_version
            break

    should_upgrade_software_version = questionary.confirm(
        "Upgrade ASA Software Version?", default=True
    ).ask()
    should_upgrade_asdm_version = questionary.confirm(
        "Upgrade ASA ASDM Version?", default=True
    ).ask()

    return UpgradeAsaDeviceInput(
        software_version=(
            selected_asa_version.software_version
            if should_upgrade_software_version
            else None
        ),
        asdm_version=(
            selected_asa_version.asdm_version if should_upgrade_asdm_version else None
        ),
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
    "--asa-uid",
    help="The UID of the ASA to list compatible versions for.",
    type=str,
    required=False,
)
@click.pass_context
def list_versions(ctx: any, asa_uid: str) -> None:
    """Retrieve the list of compatible versions for the given ASA UID."""
    # Add logic to retrieve and display the list of compatible versions
    with ApiClient(
        Configuration(host=ctx.obj["base_url"], access_token=ctx.obj["api_token"])
    ) as api_client:
        if asa_uid is None:
            asa_uid = select_asa(api_client)

        device_upgrade_service = DeviceUpgradeApiService(api_client)
        asa_versions: List[AsaCompatibleVersion] = (
            device_upgrade_service.get_compatible_asa_versions(asa_uid)
        )
        device_upgrade_service.print_asa_versions(asa_versions)


@click.command(name="upgrade")
@click.option(
    "--asa-uid",
    help="The UID of the ASA to list compatible versions for.",
    type=str,
    required=False,
)
@click.option(
    "--software-version",
    help="The software version to upgrade to",
    type=str,
    required=False,
)
@click.option(
    "--asdm-version",
    help="The ASDM version to upgrade to",
    type=str,
    required=False,
)
@click.pass_context
def upgrade(ctx: any, asa_uid: str, software_version: str, asdm_version: str) -> None:
    """Upgrade the ASA to the  specified software version and ASDM version."""
    # Add logic to retrieve and display the list of compatible versions
    with ApiClient(
        Configuration(host=ctx.obj["base_url"], access_token=ctx.obj["api_token"])
    ) as api_client:
        if asa_uid is None:
            asa_uid = select_asa(api_client)

        if software_version is None and asdm_version is None:
            asa_upgrade_input = select_asa_version(asa_uid, api_client)
        else:
            asa_upgrade_input = UpgradeAsaDeviceInput(
                software_version=software_version,
                asdm_version=asdm_version,
            )

        device_upgrade_service = DeviceUpgradeApiService(api_client)
        device_upgrade_service.upgrade_asa(asa_uid, asa_upgrade_input)

        Console().print(
            f"Successfully upgraded ASA with UID: {asa_uid} to the specified versions."
        )


cli.add_command(list_versions)
cli.add_command(upgrade)

if __name__ == "__main__":
    cli(obj={})
