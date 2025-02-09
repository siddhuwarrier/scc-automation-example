import ipaddress
from typing import List

import click
import questionary
from cdo_sdk_python import Device, ApiClient, Configuration
from rich.console import Console

from services.cli_api_service import CliApiService
from services.inventory_api_service import InventoryApiService


def validate_ip(ip: str) -> str:
    try:
        ipaddress.ip_address(ip.strip())
    except ValueError:
        raise click.BadParameter(f"Invalid IP address: {ip}")
    return ip.strip()


def validate_ips(comma_separated_ips: str) -> List[str]:
    ips = comma_separated_ips.split(",")
    return [validate_ip(ip) for ip in ips]


@click.command(
    name="add-ips-to-object-group",
    help="Add IPs to an object group",
)
@click.option(
    "--obj-name",
    help="The name of the object group to add the IPs to",
    type=str,
    required=False,
)
@click.option(
    "--obj-name",
    help="The name of the object group to add the IPs to",
    type=str,
    required=False,
)
@click.option(
    "--device-uid",
    help="The unique identifier, represented as a UUID, of the ASA device to create the object group in",
    type=str,
    required=False,
)
@click.option(
    "--ips-to-add",
    help="Comma separated list of IPs to add to the object group",
    type=str,
    required=False,
)
@click.pass_context
def add_ips_to_object_group(
    ctx: any, obj_name: str, device_uid: str, ips_to_add: str
) -> None:
    console = Console()
    with ApiClient(
        Configuration(host=ctx.obj["base_url"], access_token=ctx.obj["api_token"])
    ) as api_client:
        inventory_api_service = InventoryApiService(api_client=api_client)
        cli_api_service = CliApiService(api_client=api_client)
        if device_uid is None:
            online_asa_devices: List[Device] = inventory_api_service.get_devices(
                "deviceType:ASA AND connectivityState:ONLINE"
            )
            selected_asa_name = questionary.select(
                "Select ASA",
                choices=[device.name for device in online_asa_devices],
            ).ask()
            selected_asa_device: Device = [
                asa_device
                for asa_device in online_asa_devices
                if asa_device.name == selected_asa_name
            ][0]
        if obj_name is None:
            obj_name = questionary.text(
                "Enter the object name", default="block_network_group"
            ).ask()

        if not ips_to_add:
            ips = []
            while True:
                ip = questionary.text(
                    f"Enter an IP address to add to  {obj_name} (or press Enter to finish):"
                ).ask()
                if ip.lower() == "" and len(ips) > 0:
                    break
                elif ip.lower() == "":
                    console.print(
                        "[yellow]At least one IP address is required[/yellow]"
                    )
                    continue
                try:
                    validate_ip(ip)
                    ips.append(ip)
                except click.BadParameter as e:
                    console.print(f"[red]e[/red]")
        else:
            ips = [validate_ip(ip) for ip in ips_to_add.split(",")]

        commands = [f"object-group network {obj_name}"]
        commands.extend([f" network-object host {ip}" for ip in ips])

        cli_api_service.execute_command_and_get_result(
            [selected_asa_device.uid], "\n".join(commands)
        )
        console.print("[green]Done[/green]")
